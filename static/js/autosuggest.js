/**
 * Auto-Suggest Dropdown Component with Fuzzy Matching
 * 
 * Features:
 * - Real-time search as user types (debounced)
 * - Fuzzy matching for typos (pm kisn → PM-KISAN)
 * - Keyboard navigation (Arrow keys, Enter, Escape)
 * - Click-to-select functionality
 * - Accessible (ARIA attributes)
 * - Mobile-friendly
 * 
 * Usage:
 * <input type="text" id="scheme-search-input" placeholder="Search schemes..." />
 * <div id="suggestions-dropdown"></div>
 * 
 * <script src="autosuggest.js"></script>
 * <script>
 *   const autoSuggest = new SchemeAutoSuggest({
 *     inputId: 'scheme-search-input',
 *     dropdownId: 'suggestions-dropdown',
 *     apiEndpoint: '/api/suggestions/',
 *     onSelect: (scheme) => console.log('Selected:', scheme.title)
 *   });
 * </script>
 */

class SchemeAutoSuggest {
    constructor(options) {
        // Configuration
        this.inputId = options.inputId || 'scheme-search-input';
        this.dropdownId = options.dropdownId || 'suggestions-dropdown';
        this.apiEndpoint = options.apiEndpoint || '/api/suggestions/';
        this.minChars = options.minChars || 2;
        this.debounceMs = options.debounceMs || 300;
        this.maxSuggestions = options.maxSuggestions || 10;
        this.onSelect = options.onSelect || null;
        this.onSearch = options.onSearch || null;
        
        // State
        this.suggestions = [];
        this.selectedIndex = -1;
        this.debounceTimer = null;
        this.isLoading = false;
        
        // DOM elements
        this.input = document.getElementById(this.inputId);
        this.dropdown = document.getElementById(this.dropdownId);
        
        if (!this.input || !this.dropdown) {
            console.error('SchemeAutoSuggest: Input or dropdown element not found');
            return;
        }
        
        // Initialize
        this.init();
    }
    
    init() {
        // Set up event listeners
        this.input.addEventListener('input', (e) => this.handleInput(e));
        this.input.addEventListener('keydown', (e) => this.handleKeyDown(e));
        this.input.addEventListener('focus', (e) => this.handleFocus(e));
        this.input.addEventListener('blur', (e) => this.handleBlur(e));
        
        // Close dropdown when clicking outside
        document.addEventListener('click', (e) => {
            if (!this.input.contains(e.target) && !this.dropdown.contains(e.target)) {
                this.hideDropdown();
            }
        });
        
        // Set ARIA attributes
        this.input.setAttribute('aria-autocomplete', 'list');
        this.input.setAttribute('aria-controls', this.dropdownId);
        this.input.setAttribute('aria-expanded', 'false');
        
        this.dropdown.setAttribute('role', 'listbox');
        this.dropdown.style.display = 'none';
        
        console.log('SchemeAutoSuggest initialized');
    }
    
    handleInput(e) {
        const query = e.target.value.trim();
        
        // Clear previous timer
        if (this.debounceTimer) {
            clearTimeout(this.debounceTimer);
        }
        
        // Hide dropdown if query too short
        if (query.length < this.minChars) {
            this.hideDropdown();
            return;
        }
        
        // Debounce: wait for user to stop typing
        this.debounceTimer = setTimeout(() => {
            this.fetchSuggestions(query);
        }, this.debounceMs);
    }
    
    handleKeyDown(e) {
        if (!this.dropdown || this.dropdown.style.display === 'none') {
            return;
        }
        
        switch (e.key) {
            case 'ArrowDown':
                e.preventDefault();
                this.selectNext();
                break;
            case 'ArrowUp':
                e.preventDefault();
                this.selectPrevious();
                break;
            case 'Enter':
                e.preventDefault();
                this.selectCurrent();
                break;
            case 'Escape':
                e.preventDefault();
                this.hideDropdown();
                break;
        }
    }
    
    handleFocus(e) {
        // Show dropdown if there are cached suggestions
        if (this.suggestions.length > 0) {
            this.showDropdown();
        }
    }
    
    handleBlur(e) {
        // Delay hiding to allow click on suggestion
        setTimeout(() => {
            this.hideDropdown();
        }, 200);
    }
    
    async fetchSuggestions(query) {
        try {
            this.isLoading = true;
            this.showLoadingState();
            
            // Call API
            const response = await fetch(this.apiEndpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    partial_text: query,
                    max_suggestions: this.maxSuggestions
                })
            });
            
            if (!response.ok) {
                throw new Error(`API error: ${response.status}`);
            }
            
            const data = await response.json();
            
            this.suggestions = data.suggestions || [];
            this.selectedIndex = -1;
            
            this.renderSuggestions();
            this.showDropdown();
            
            this.isLoading = false;
            
        } catch (error) {
            console.error('Failed to fetch suggestions:', error);
            this.isLoading = false;
            this.showErrorState();
        }
    }
    
    renderSuggestions() {
        if (this.suggestions.length === 0) {
            this.dropdown.innerHTML = '<div class="no-suggestions">No schemes found</div>';
            return;
        }
        
        let html = '<ul class="suggestions-list">';
        
        this.suggestions.forEach((suggestion, index) => {
            const isSelected = index === this.selectedIndex;
            const matchType = suggestion.match_type || 'fuzzy';
            const score = suggestion.score || 0;
            
            html += `
                <li class="suggestion-item ${isSelected ? 'selected' : ''}"
                    data-index="${index}"
                    data-id="${suggestion.id}"
                    role="option"
                    aria-selected="${isSelected}">
                    <div class="suggestion-title">${this.highlightMatch(suggestion.title)}</div>
                    ${matchType === 'fuzzy' ? '<span class="match-badge">✓ Fuzzy match</span>' : ''}
                </li>
            `;
        });
        
        html += '</ul>';
        
        this.dropdown.innerHTML = html;
        
        // Add click listeners to all suggestions
        const items = this.dropdown.querySelectorAll('.suggestion-item');
        items.forEach((item, index) => {
            item.addEventListener('click', () => {
                this.selectIndex(index);
            });
        });
    }
    
    highlightMatch(title) {
        // Simple highlighting - can be improved
        const query = this.input.value.trim();
        if (!query) return title;
        
        const regex = new RegExp(`(${this.escapeRegex(query)})`, 'gi');
        return title.replace(regex, '<strong>$1</strong>');
    }
    
    escapeRegex(str) {
        return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    }
    
    showLoadingState() {
        this.dropdown.innerHTML = '<div class="loading-suggestions">Loading...</div>';
        this.showDropdown();
    }
    
    showErrorState() {
        this.dropdown.innerHTML = '<div class="error-suggestions">Failed to load suggestions</div>';
        this.showDropdown();
    }
    
    showDropdown() {
        this.dropdown.style.display = 'block';
        this.input.setAttribute('aria-expanded', 'true');
    }
    
    hideDropdown() {
        this.dropdown.style.display = 'none';
        this.input.setAttribute('aria-expanded', 'false');
        this.selectedIndex = -1;
    }
    
    selectNext() {
        if (this.selectedIndex < this.suggestions.length - 1) {
            this.selectedIndex++;
            this.updateSelection();
        }
    }
    
    selectPrevious() {
        if (this.selectedIndex > 0) {
            this.selectedIndex--;
            this.updateSelection();
        }
    }
    
    updateSelection() {
        const items = this.dropdown.querySelectorAll('.suggestion-item');
        items.forEach((item, index) => {
            if (index === this.selectedIndex) {
                item.classList.add('selected');
                item.setAttribute('aria-selected', 'true');
                item.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
            } else {
                item.classList.remove('selected');
                item.setAttribute('aria-selected', 'false');
            }
        });
    }
    
    selectCurrent() {
        if (this.selectedIndex >= 0 && this.selectedIndex < this.suggestions.length) {
            this.selectIndex(this.selectedIndex);
        }
    }
    
    selectIndex(index) {
        const selected = this.suggestions[index];
        if (!selected) return;
        
        // Update input value
        this.input.value = selected.title;
        
        // Hide dropdown
        this.hideDropdown();
        
        // Call onSelect callback
        if (this.onSelect) {
            this.onSelect(selected);
        }
        
        // Trigger search if callback provided
        if (this.onSearch) {
            this.onSearch(selected.title);
        }
    }
    
    clear() {
        this.input.value = '';
        this.suggestions = [];
        this.selectedIndex = -1;
        this.hideDropdown();
    }
}

// CSS Styles (inject into page or include in stylesheet)
const autoSuggestStyles = `
<style>
    /* Auto-Suggest Dropdown Styles */
    #suggestions-dropdown {
        position: absolute;
        z-index: 1000;
        background: white;
        border: 1px solid #ddd;
        border-top: none;
        border-radius: 0 0 4px 4px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        max-height: 300px;
        overflow-y: auto;
        width: 100%;
        margin-top: -1px;
    }
    
    .suggestions-list {
        list-style: none;
        margin: 0;
        padding: 0;
    }
    
    .suggestion-item {
        padding: 12px 16px;
        cursor: pointer;
        border-bottom: 1px solid #f0f0f0;
        transition: background-color 0.2s;
    }
    
    .suggestion-item:hover,
    .suggestion-item.selected {
        background-color: #f5f5f5;
    }
    
    .suggestion-item.selected {
        background-color: #e3f2fd;
    }
    
    .suggestion-title {
        font-size: 14px;
        color: #333;
        margin-bottom: 4px;
    }
    
    .suggestion-title strong {
        color: #1976d2;
        font-weight: 600;
    }
    
    .match-badge {
        font-size: 11px;
        color: #4caf50;
        background: #e8f5e9;
        padding: 2px 6px;
        border-radius: 3px;
        display: inline-block;
    }
    
    .loading-suggestions,
    .error-suggestions,
    .no-suggestions {
        padding: 12px 16px;
        text-align: center;
        color: #666;
        font-size: 13px;
    }
    
    .error-suggestions {
        color: #f44336;
    }
    
    /* Input styling */
    #scheme-search-input {
        width: 100%;
        padding: 12px 16px;
        font-size: 16px;
        border: 1px solid #ddd;
        border-radius: 4px;
        outline: none;
        transition: border-color 0.3s;
    }
    
    #scheme-search-input:focus {
        border-color: #1976d2;
        box-shadow: 0 0 0 3px rgba(25, 118, 210, 0.1);
    }
</style>
`;

// Export for use in modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SchemeAutoSuggest;
}
