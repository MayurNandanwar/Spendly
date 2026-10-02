const PptxGenJS = require('pptxgenjs');

const pres = new PptxGenJS();
pres.layout = 'LAYOUT_16x9';
pres.defineLayout({ name: 'LAYOUT_16x9', width: 10, height: 5.625 });

// Color palette - Professional teal & navy theme
const colors = {
  primary: '028090',      // Teal
  secondary: '00A896',    // Seafoam
  accent: '02C39A',       // Mint
  dark: '1E2761',         // Navy
  light: 'F5F5F5',        // Off-white
  white: 'FFFFFF',
  text: '333333',
  lightText: '666666',
  success: '52B788',
  danger: 'D62828'
};

// Helper functions
const addTitleSlide = (title, subtitle) => {
  const slide = pres.addSlide();
  slide.background = { color: colors.primary };

  slide.addText(title, {
    x: 0.5,
    y: 2,
    w: 9,
    h: 1,
    fontSize: 52,
    bold: true,
    color: colors.white,
    fontFace: 'Cambria',
    align: 'center'
  });

  slide.addText(subtitle, {
    x: 0.5,
    y: 3.2,
    w: 9,
    h: 1,
    fontSize: 28,
    color: colors.accent,
    fontFace: 'Calibri',
    align: 'center'
  });

  // Decorative line
  slide.addShape('rect', {
    x: 3,
    y: 4.3,
    w: 4,
    h: 0.05,
    fill: { color: colors.accent },
    line: { type: 'none' }
  });
};

const addContentSlide = (title, content) => {
  const slide = pres.addSlide();
  slide.background = { color: colors.white };

  // Header bar
  slide.addShape('rect', {
    x: 0,
    y: 0,
    w: 10,
    h: 0.8,
    fill: { color: colors.primary },
    line: { type: 'none' }
  });

  // Title
  slide.addText(title, {
    x: 0.5,
    y: 0.15,
    w: 9,
    h: 0.5,
    fontSize: 40,
    bold: true,
    color: colors.white,
    fontFace: 'Cambria',
    align: 'left',
    valign: 'middle'
  });

  // Content
  if (Array.isArray(content)) {
    let y = 1.2;
    content.forEach((item) => {
      if (item.type === 'heading') {
        slide.addText(item.text, {
          x: 0.7,
          y: y,
          w: 8.6,
          h: 0.4,
          fontSize: 20,
          bold: true,
          color: colors.primary,
          fontFace: 'Cambria'
        });
        y += 0.5;
      } else if (item.type === 'bullet') {
        slide.addText('• ' + item.text, {
          x: 0.9,
          y: y,
          w: 8.1,
          h: 0.35,
          fontSize: 16,
          color: colors.text,
          fontFace: 'Calibri'
        });
        y += 0.45;
      } else if (item.type === 'subtext') {
        slide.addText(item.text, {
          x: 1.2,
          y: y,
          w: 7.8,
          h: 0.3,
          fontSize: 14,
          color: colors.lightText,
          fontFace: 'Calibri',
          italic: true
        });
        y += 0.35;
      } else if (item.type === 'space') {
        y += 0.3;
      }
    });
  }
};

const addTwoColumnSlide = (title, leftContent, rightContent) => {
  const slide = pres.addSlide();
  slide.background = { color: colors.white };

  // Header bar
  slide.addShape('rect', {
    x: 0,
    y: 0,
    w: 10,
    h: 0.8,
    fill: { color: colors.primary },
    line: { type: 'none' }
  });

  // Title
  slide.addText(title, {
    x: 0.5,
    y: 0.15,
    w: 9,
    h: 0.5,
    fontSize: 40,
    bold: true,
    color: colors.white,
    fontFace: 'Cambria',
    align: 'left',
    valign: 'middle'
  });

  // Left column
  let y = 1.2;
  leftContent.forEach(item => {
    if (item.type === 'heading') {
      slide.addText(item.text, {
        x: 0.5,
        y: y,
        w: 4.3,
        h: 0.4,
        fontSize: 18,
        bold: true,
        color: colors.primary,
        fontFace: 'Cambria'
      });
      y += 0.45;
    } else if (item.type === 'bullet') {
      slide.addText('• ' + item.text, {
        x: 0.7,
        y: y,
        w: 4.1,
        h: 0.4,
        fontSize: 14,
        color: colors.text,
        fontFace: 'Calibri'
      });
      y += 0.45;
    }
  });

  // Right column
  y = 1.2;
  rightContent.forEach(item => {
    if (item.type === 'heading') {
      slide.addText(item.text, {
        x: 5.2,
        y: y,
        w: 4.3,
        h: 0.4,
        fontSize: 18,
        bold: true,
        color: colors.primary,
        fontFace: 'Cambria'
      });
      y += 0.45;
    } else if (item.type === 'bullet') {
      slide.addText('• ' + item.text, {
        x: 5.4,
        y: y,
        w: 4.1,
        h: 0.4,
        fontSize: 14,
        color: colors.text,
        fontFace: 'Calibri'
      });
      y += 0.45;
    }
  });
};

// Slide 1: Title Slide
addTitleSlide('Spendly', 'Personal Expense Tracker - App Workflow');

// Slide 2: Project Overview
addContentSlide('Project Overview', [
  { type: 'heading', text: 'What is Spendly?' },
  { type: 'bullet', text: 'A lightweight personal expense tracking application' },
  { type: 'bullet', text: 'Built with Flask (Python web framework) and SQLite database' },
  { type: 'bullet', text: 'User-friendly interface for managing personal finances' },
  { type: 'space' },
  { type: 'heading', text: 'Key Features' },
  { type: 'bullet', text: 'User authentication and account management' },
  { type: 'bullet', text: 'Expense tracking with categories and dates' },
  { type: 'bullet', text: 'Dashboard with filtering and expense summaries' },
  { type: 'bullet', text: 'Edit and delete expense functionality' }
]);

// Slide 3: Technology Stack
addTwoColumnSlide('Technology Stack',
  [
    { type: 'heading', text: 'Backend' },
    { type: 'bullet', text: 'Flask - Web framework' },
    { type: 'bullet', text: 'SQLite - Database' },
    { type: 'bullet', text: 'Bcrypt - Password hashing' },
    { type: 'bullet', text: 'Python 3.10+' }
  ],
  [
    { type: 'heading', text: 'Frontend' },
    { type: 'bullet', text: 'HTML5 & Jinja2 templates' },
    { type: 'bullet', text: 'CSS3 with design tokens' },
    { type: 'bullet', text: 'Vanilla JavaScript (no frameworks)' },
    { type: 'bullet', text: 'Responsive design' }
  ]
);

// Slide 4: Database Schema
addContentSlide('Database Schema', [
  { type: 'heading', text: 'Users Table' },
  { type: 'bullet', text: 'id - Auto-incrementing user ID' },
  { type: 'bullet', text: 'name - User\'s display name' },
  { type: 'bullet', text: 'email - Unique email for login' },
  { type: 'bullet', text: 'password_hash - Bcrypt-hashed password' },
  { type: 'bullet', text: 'created_at - Account creation timestamp' },
  { type: 'space' },
  { type: 'heading', text: 'Expenses Table' },
  { type: 'bullet', text: 'id - Auto-incrementing expense ID' },
  { type: 'bullet', text: 'user_id - Foreign key to users' },
  { type: 'bullet', text: 'amount - Expense amount (REAL)' },
  { type: 'bullet', text: 'category - Category (Food, Transport, Bills)' },
  { type: 'bullet', text: 'date - Expense date (YYYY-MM-DD format)' }
]);

// Slide 5: Project Structure
addContentSlide('Project Structure', [
  { type: 'bullet', text: 'app.py - All Flask routes (single file, no blueprints)' },
  { type: 'bullet', text: 'database/db.py - SQLite helpers (get_db, init_db, seed_db)' },
  { type: 'bullet', text: 'templates/ - Jinja2 templates (base, landing, login, register, profile)' },
  { type: 'bullet', text: 'static/css/ - Global styles (style.css) and page-specific styles' },
  { type: 'bullet', text: 'static/js/ - Vanilla JavaScript utilities' },
  { type: 'space' },
  { type: 'heading', text: 'Design System' },
  { type: 'bullet', text: 'CSS design tokens defined in :root of style.css' },
  { type: 'bullet', text: 'Consistent colors, fonts, and border radius across all pages' }
]);

// Slide 6: Authentication Flow
addTwoColumnSlide('Authentication Flow',
  [
    { type: 'heading', text: 'Landing Page' },
    { type: 'bullet', text: 'Logged-out users see marketing page' },
    { type: 'bullet', text: 'Links to Register and Login' }
  ],
  [
    { type: 'heading', text: 'Registration & Login' },
    { type: 'bullet', text: 'Form validation' },
    { type: 'bullet', text: 'Bcrypt password hashing' },
    { type: 'bullet', text: 'Session-based authentication' }
  ]
);

// Slide 7: Implemented Routes (Part 1)
addContentSlide('Implemented Routes - Part 1', [
  { type: 'heading', text: 'GET /' },
  { type: 'bullet', text: 'Renders landing page (logged-out users)' },
  { type: 'bullet', text: 'Logged-in users redirected to /profile' },
  { type: 'space' },
  { type: 'heading', text: 'GET /register & POST /register' },
  { type: 'bullet', text: 'Registration form with validation' },
  { type: 'bullet', text: 'Password strength checking' },
  { type: 'bullet', text: 'Account creation with bcrypt hashing' },
  { type: 'space' },
  { type: 'heading', text: 'GET /login & POST /login' },
  { type: 'bullet', text: 'Login form with validation' },
  { type: 'bullet', text: 'Session management' }
]);

// Slide 8: Implemented Routes (Part 2)
addContentSlide('Implemented Routes - Part 2', [
  { type: 'heading', text: 'POST /logout' },
  { type: 'bullet', text: 'Clears session and redirects to landing page' },
  { type: 'space' },
  { type: 'heading', text: 'GET /profile (COMPLETED - Step 3)' },
  { type: 'bullet', text: 'Consolidated dashboard + account settings' },
  { type: 'bullet', text: 'Displays user header with name and email' },
  { type: 'bullet', text: 'Shows expense list with filters (date range, category)' },
  { type: 'bullet', text: 'Displays expense summary (total spent)' },
  { type: 'bullet', text: 'Account information section' }
]);

// Slide 9: Future Routes
addContentSlide('Future Routes - To Be Implemented', [
  { type: 'heading', text: 'Step 7: Add Expense' },
  { type: 'bullet', text: 'GET /expenses/add - Form to add new expense' },
  { type: 'bullet', text: 'POST /expenses/add - Save expense to database' },
  { type: 'space' },
  { type: 'heading', text: 'Step 8: Edit Expense' },
  { type: 'bullet', text: 'GET /expenses/<id>/edit - Form to edit expense' },
  { type: 'bullet', text: 'POST /expenses/<id>/edit - Update expense' },
  { type: 'space' },
  { type: 'heading', text: 'Step 9: Delete Expense' },
  { type: 'bullet', text: 'GET /expenses/<id>/delete - Delete expense' }
]);

// Slide 10: User Workflow
const slide10 = pres.addSlide();
slide10.background = { color: colors.white };

slide10.addShape('rect', {
  x: 0,
  y: 0,
  w: 10,
  h: 0.8,
  fill: { color: colors.primary },
  line: { type: 'none' }
});

slide10.addText('User Workflow', {
  x: 0.5,
  y: 0.15,
  w: 9,
  h: 0.5,
  fontSize: 40,
  bold: true,
  color: colors.white,
  fontFace: 'Cambria',
  align: 'left',
  valign: 'middle'
});

const steps = [
  { num: '1', title: 'Visit Landing', desc: 'User lands on marketing page' },
  { num: '2', title: 'Register/Login', desc: 'Create account or sign in' },
  { num: '3', title: 'Dashboard', desc: 'View expenses and summary' },
  { num: '4', title: 'Manage', desc: 'Add, edit, delete expenses' },
  { num: '5', title: 'Filter & Track', desc: 'Filter by date and category' }
];

let xPos = 0.4;
steps.forEach((step, index) => {
  // Circle with number
  slide10.addShape('ellipse', {
    x: xPos,
    y: 1.5,
    w: 0.6,
    h: 0.6,
    fill: { color: colors.primary },
    line: { color: colors.primary, width: 2 }
  });

  slide10.addText(step.num, {
    x: xPos,
    y: 1.5,
    w: 0.6,
    h: 0.6,
    fontSize: 20,
    bold: true,
    color: colors.white,
    fontFace: 'Calibri',
    align: 'center',
    valign: 'middle'
  });

  // Arrow (except for last)
  if (index < steps.length - 1) {
    slide10.addText('→', {
      x: xPos + 0.65,
      y: 1.55,
      w: 0.3,
      h: 0.5,
      fontSize: 20,
      color: colors.primary,
      fontFace: 'Calibri',
      align: 'center'
    });
  }

  // Title and description
  slide10.addText(step.title, {
    x: xPos - 0.1,
    y: 2.3,
    w: 0.8,
    h: 0.3,
    fontSize: 12,
    bold: true,
    color: colors.primary,
    fontFace: 'Calibri',
    align: 'center'
  });

  slide10.addText(step.desc, {
    x: xPos - 0.2,
    y: 2.65,
    w: 1,
    h: 0.5,
    fontSize: 10,
    color: colors.lightText,
    fontFace: 'Calibri',
    align: 'center'
  });

  xPos += 1.9;
});

// Slide 11: Security & Best Practices
addContentSlide('Security & Best Practices', [
  { type: 'heading', text: 'Authentication & Password' },
  { type: 'bullet', text: 'Bcrypt hashing for password security' },
  { type: 'bullet', text: 'Session-based authentication with Flask session' },
  { type: 'space' },
  { type: 'heading', text: 'Database' },
  { type: 'bullet', text: 'Foreign key enforcement enabled (PRAGMA foreign_keys = ON)' },
  { type: 'bullet', text: 'Parameterized queries to prevent SQL injection' },
  { type: 'space' },
  { type: 'heading', text: 'Code Quality' },
  { type: 'bullet', text: 'PEP 8 compliant Python code' },
  { type: 'bullet', text: 'Proper error handling with Flask abort()' },
  { type: 'bullet', text: 'URL generation with url_for() (no hardcoded URLs)' }
]);

// Slide 12: Design System
addContentSlide('Design System', [
  { type: 'heading', text: 'Color Palette' },
  { type: 'bullet', text: 'Primary (Teal): #028090 - Main navigation and headers' },
  { type: 'bullet', text: 'Secondary (Seafoam): #00A896 - Accent elements' },
  { type: 'bullet', text: 'Accent (Mint): #02C39A - Highlights and CTAs' },
  { type: 'space' },
  { type: 'heading', text: 'Typography & Layout' },
  { type: 'bullet', text: 'Consistent font stack (system fonts)' },
  { type: 'bullet', text: 'Responsive design for mobile and desktop' },
  { type: 'bullet', text: 'Proper spacing and visual hierarchy' }
]);

// Slide 13: Testing & Development
addContentSlide('Testing & Development', [
  { type: 'heading', text: 'Development Environment' },
  { type: 'bullet', text: 'Run on port 5001: python app.py' },
  { type: 'bullet', text: 'Demo user: demo@spendly.com / demo123' },
  { type: 'space' },
  { type: 'heading', text: 'Testing' },
  { type: 'bullet', text: 'Run all tests: pytest' },
  { type: 'bullet', text: 'Run specific test: pytest -k "test_name"' },
  { type: 'bullet', text: 'Display output: pytest -s' },
  { type: 'space' },
  { type: 'heading', text: 'Key Constraints' },
  { type: 'bullet', text: 'Flask only (no FastAPI, Django)' },
  { type: 'bullet', text: 'SQLite only (no PostgreSQL, ORM)' },
  { type: 'bullet', text: 'Vanilla JavaScript only (no frameworks)' }
]);

// Slide 14: Summary & Next Steps
const slide14 = pres.addSlide();
slide14.background = { color: colors.primary };

slide14.addText('Summary', {
  x: 0.5,
  y: 0.5,
  w: 9,
  h: 0.6,
  fontSize: 48,
  bold: true,
  color: colors.white,
  fontFace: 'Cambria',
  align: 'center'
});

slide14.addText('Spendly is a clean, modern expense tracker built with Flask and SQLite.\nWith a focus on security, simplicity, and user experience.', {
  x: 0.5,
  y: 1.4,
  w: 9,
  h: 0.8,
  fontSize: 18,
  color: colors.accent,
  fontFace: 'Calibri',
  align: 'center'
});

slide14.addText('Completed Features:', {
  x: 1,
  y: 2.4,
  w: 8,
  h: 0.4,
  fontSize: 16,
  bold: true,
  color: colors.white,
  fontFace: 'Cambria'
});

slide14.addText('✓ User authentication  |  ✓ Dashboard  |  ✓ Expense tracking  |  ✓ Responsive design', {
  x: 1,
  y: 2.9,
  w: 8,
  h: 0.5,
  fontSize: 14,
  color: colors.light,
  fontFace: 'Calibri',
  align: 'center'
});

slide14.addText('Ready for expense management and filtering features in upcoming releases', {
  x: 0.5,
  y: 3.8,
  w: 9,
  h: 0.7,
  fontSize: 16,
  italic: true,
  color: colors.light,
  fontFace: 'Calibri',
  align: 'center'
});

// Write the presentation
pres.writeFile('Spendly_App_Workflow.pptx');
console.log('Presentation created: Spendly_App_Workflow.pptx');
