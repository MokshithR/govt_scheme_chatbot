"""
Django management command to generate and store embeddings for all government schemes.

Usage:
    python manage.py generate_embeddings [--batch-size 5] [--force]

This command:
1. Fetches all schemes from the database without embeddings
2. Generates 768-dimensional embeddings using sentence-transformers
3. Stores embeddings in the PostgreSQL database using pgvector
4. Supports batch processing with progress tracking
"""

import time
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction, connection
from chatbot.models import GovernmentScheme
from chatbot.embedding_utils import prepare_embedding_text, create_embedding, validate_embedding


class Command(BaseCommand):
    help = 'Generate and store sentence-transformers embeddings for all government schemes'

    def add_arguments(self, parser):
        parser.add_argument(
            '--batch-size',
            type=int,
            default=5,
            help='Number of schemes to process in each batch (default: 5)',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Regenerate embeddings for schemes that already have them',
        )
        parser.add_argument(
            '--scheme-id',
            type=int,
            help='Generate embedding for a specific scheme ID only',
        )

    def handle(self, *args, **options):
        batch_size = options['batch_size']
        force_update = options['force']
        scheme_id = options.get('scheme_id')
        
        # Get schemes to process
        if scheme_id:
            schemes = GovernmentScheme.objects.filter(id=scheme_id)
            if not schemes.exists():
                raise CommandError(f'Scheme with ID {scheme_id} not found')
            self.stdout.write(f'Processing single scheme: ID {scheme_id}')
        elif force_update:
            schemes = GovernmentScheme.objects.all().order_by('id')
            self.stdout.write(f'Processing all {schemes.count()} schemes (regenerating embeddings)')
        else:
            # Only process schemes without embeddings
            # Check using raw SQL since embedding is a pgvector field
            schemes = GovernmentScheme.objects.raw(
                'SELECT * FROM scheme WHERE embedding IS NULL ORDER BY id'
            )
            schemes_list = list(schemes)
            self.stdout.write(f'Processing {len(schemes_list)} schemes without embeddings')
            schemes = schemes_list
        
        if not schemes:
            self.stdout.write(self.style.WARNING('No schemes to process'))
            return
        
        total = len(schemes) if isinstance(schemes, list) else schemes.count()
        processed = 0
        errors = 0
        skipped = 0
        
        self.stdout.write(f'Starting embedding generation for {total} schemes...\n')
        
        # Process in batches
        for i in range(0, total, batch_size):
            batch = schemes[i:i + batch_size] if isinstance(schemes, list) else list(schemes[i:i + batch_size])
            
            for scheme in batch:
                try:
                    # Skip if embedding already exists and not forcing update
                    if not force_update:
                        # Check if embedding exists
                        with connection.cursor() as cursor:
                            cursor.execute(
                                'SELECT embedding IS NOT NULL FROM scheme WHERE id = %s',
                                [scheme.id]
                            )
                            has_embedding = cursor.fetchone()[0]
                            if has_embedding:
                                skipped += 1
                                self.stdout.write(
                                    self.style.WARNING(
                                        f'  ⊘ Scheme {scheme.id}: Skipped (already has embedding)'
                                    )
                                )
                                continue
                    
                    # Prepare text for embedding from all relevant fields
                    embedding_text = prepare_embedding_text(scheme)
                    
                    if not embedding_text or not embedding_text.strip():
                        self.stdout.write(
                            self.style.WARNING(
                                f'  ⊘ Scheme {scheme.id}: Skipped (no text content)'
                            )
                        )
                        skipped += 1
                        continue
                    
                    # Generate embedding using sentence-transformers
                    embedding_vector = create_embedding(embedding_text)
                    
                    if embedding_vector is None:
                        self.stdout.write(
                            self.style.ERROR(
                                f'  ✗ Scheme {scheme.id}: Failed to generate embedding'
                            )
                        )
                        errors += 1
                        continue
                    
                    # Validate embedding
                    if not validate_embedding(embedding_vector):
                        self.stdout.write(
                            self.style.ERROR(
                                f'  ✗ Scheme {scheme.id}: Invalid embedding generated'
                            )
                        )
                        errors += 1
                        continue
                    
                    # Store embedding in database using raw SQL
                    # Convert Python list to PostgreSQL vector format
                    vector_str = '[' + ','.join(map(str, embedding_vector)) + ']'
                    
                    with transaction.atomic():
                        with connection.cursor() as cursor:
                            cursor.execute(
                                """
                                UPDATE scheme 
                                SET embedding = %s::vector 
                                WHERE id = %s
                                """,
                                [vector_str, scheme.id]
                            )
                    
                    processed += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'  ✓ Scheme {scheme.id}: "{scheme.title[:50]}..." - Embedding generated'
                        )
                    )
                    
                except Exception as e:
                    errors += 1
                    self.stdout.write(
                        self.style.ERROR(
                            f'  ✗ Scheme {scheme.id}: Error - {str(e)}'
                        )
                    )
            
            # Small delay between batches for stability
            if i + batch_size < total:
                self.stdout.write(f'\nWaiting 1 second before next batch...\n')
                time.sleep(1)
        
        # Summary
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.SUCCESS(f'✓ Successfully processed: {processed} schemes'))
        if skipped > 0:
            self.stdout.write(self.style.WARNING(f'⊘ Skipped: {skipped} schemes'))
        if errors > 0:
            self.stdout.write(self.style.ERROR(f'✗ Errors: {errors} schemes'))
        self.stdout.write('=' * 60)
        
        if processed > 0:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n✓ Successfully generated {processed} embeddings!'
                )
            )
            self.stdout.write(
                'You can now use vector similarity search in your application.'
            )
