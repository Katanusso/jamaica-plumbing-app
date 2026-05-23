# Jamaica Plumbing App - Phase 1 Fixed Files

Copy these files into your existing project, keeping the same folder structure.

Main fixes:
- Corrected User.id vs Plumber.id confusion.
- Fixed CSV upload so services are saved under the plumber profile.
- Fixed view_services so uploaded services and prices appear.
- Fixed login template variable.
- Fixed SQLite path to use instance/app.db.
- Added ALLOWED_EXTENSIONS for CSV uploads.
- Added a public browse services page for demo use.
- Cleaned navigation so logged-out users see Login/Register instead of protected pages.

After copying:
1. Open a terminal in the project folder.
2. Activate venv.
3. Run: flask run
4. Visit: http://127.0.0.1:5000
