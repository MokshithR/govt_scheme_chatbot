// MongoDB Compass Commands to Delete Schemes from Database
// Copy and paste these commands in MongoDB Compass MongoDB Shell

// Use the Govt_schemes database
use('Govt_schemes');

// ========================================
// OPTION 1: DELETE ALL SCHEMES (COMPLETE RESET)
// ========================================
// WARNING: This will delete ALL schemes in the database
// Uncomment the line below to delete everything
// db.government_schemes.deleteMany({});

// ========================================
// OPTION 2: DELETE BY SPECIFIC CRITERIA
// ========================================

// Delete all Central Government schemes
db.government_schemes.deleteMany({"government_level": "central"});

// Delete all State Government schemes
// db.government_schemes.deleteMany({"government_level": "state"});

// Delete schemes by specific sector
// db.government_schemes.deleteMany({"sector": "agriculture"});
// db.government_schemes.deleteMany({"sector": "health"});
// db.government_schemes.deleteMany({"sector": "education"});
// db.government_schemes.deleteMany({"sector": "employment"});

// Delete schemes by state (e.g., Karnataka schemes)
// db.government_schemes.deleteMany({"state": "Karnataka"});

// Delete inactive schemes
// db.government_schemes.deleteMany({"is_active": false});

// ========================================
// OPTION 3: DELETE SPECIFIC SCHEMES BY TITLE
// ========================================

// Delete specific scheme by exact title
// db.government_schemes.deleteOne({"title": "Kisan Credit Card (KCC) Scheme"});

// Delete multiple specific schemes
// db.government_schemes.deleteMany({
//   "title": {
//     "$in": [
//       "Kisan Credit Card (KCC) Scheme",
//       "Mahatma Gandhi National Rural Employment Guarantee Act (MGNREGA)",
//       "National Scholarship Portal (NSP)"
//     ]
//   }
// });

// ========================================
// OPTION 4: DELETE RECENTLY ADDED SCHEMES
// ========================================

// Delete schemes added today
// db.government_schemes.deleteMany({
//   "created_at": {
//     "$gte": new Date(new Date().setHours(0,0,0,0))
//   }
// });

// Delete schemes added in the last hour
// db.government_schemes.deleteMany({
//   "created_at": {
//     "$gte": new Date(Date.now() - 60*60*1000)
//   }
// });

// ========================================
// OPTION 5: DELETE BY MINISTRY
// ========================================

// Delete schemes from specific ministry
// db.government_schemes.deleteMany({"ministry": "Ministry of Agriculture and Farmers Welfare"});

// ========================================
// VERIFICATION COMMANDS
// ========================================

// Check total count after deletion
db.government_schemes.countDocuments({});

// Check remaining schemes by sector
db.government_schemes.aggregate([
  { $group: { _id: "$sector", count: { $sum: 1 } } },
  { $sort: { count: -1 } }
]);

// Check remaining schemes by government level
db.government_schemes.aggregate([
  { $group: { _id: "$government_level", count: { $sum: 1 } } },
  { $sort: { count: -1 } }
]);

// List all remaining scheme titles
db.government_schemes.find({}, {"title": 1, "sector": 1, "_id": 0}).sort({"title": 1});

// ========================================
// BACKUP BEFORE DELETION (RECOMMENDED)
// ========================================

// Export all schemes to backup before deletion
// Run this in terminal/command prompt:
// mongoexport --db=Govt_schemes --collection=government_schemes --out=backup_schemes.json

// To restore from backup:
// mongoimport --db=Govt_schemes --collection=government_schemes --file=backup_schemes.json
