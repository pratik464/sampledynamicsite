# InkFlow — Blog Management System

A full-featured blog management website built with Python Flask.

## Features

- **5 Pages:** Home/Blog, Post Detail, Dashboard, Post Editor, Auth (Login/Register) + Profile
- Rich text editor with toolbar (Bold, Italic, Headings, Lists, Blockquote, Links)
- Image upload for cover photos
- Comment system (no login required to comment)
- Author dashboard with stats (posts, views, comments)
- Search and category filtering
- Pagination
- User authentication (register, login, logout)
- Profile management
- Responsive design (mobile-friendly)
- Demo data seeded on first run

## Setup

### 1. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the app

```bash
python app.py
```

### 3. Open in browser

```
http://127.0.0.1:5000
```

## Demo Login

| Field    | Value     |
|----------|-----------|
| Username | `admin`   |
| Password | `admin123`|

## Project Structure

```
blog_app/
├── app.py                  # Main Flask application
├── requirements.txt        # Python dependencies
├── blog.db                 # SQLite database (auto-created)
├── templates/
│   ├── base.html           # Layout with nav & footer
│   ├── index.html          # Page 1: Home / Blog list
│   ├── post_detail.html    # Page 2: Single post + comments
│   ├── dashboard.html      # Page 3: Author dashboard
│   ├── post_editor.html    # Page 4: Create / edit posts
│   ├── auth.html           # Page 5: Login + Register
│   ├── profile.html        # Profile management
│   └── 404.html            # Error page
└── static/
    ├── css/style.css       # Full stylesheet
    ├── js/main.js          # Rich editor + interactions
    └── uploads/            # Uploaded cover images
```

## Pages Overview

| # | URL | Description |
|---|-----|-------------|
| 1 | `/` | Blog home — featured posts, search, category filter, pagination |
| 2 | `/post/<slug>` | Post detail — content, comments, related posts |
| 3 | `/dashboard` | Author dashboard — stats, post table, recent comments |
| 4 | `/post/new` or `/post/<id>/edit` | Rich text post editor |
| 5 | `/login` & `/register` | Authentication |
| + | `/profile` | Edit profile, view your posts |
