// ── FLASH AUTO-DISMISS ─────────────────────────────────
document.querySelectorAll('.flash').forEach(el => {
  setTimeout(() => { el.style.transition='opacity .5s'; el.style.opacity='0'; setTimeout(()=>el.remove(), 500); }, 4000);
});

// ── RICH TEXT EDITOR ───────────────────────────────────
const editor = document.getElementById('editor');
const hiddenInput = document.getElementById('content-hidden');

if (editor && hiddenInput) {
  // Sync to hidden input before form submit
  editor.closest('form').addEventListener('submit', () => {
    hiddenInput.value = editor.innerHTML;
  });

  // Toolbar buttons
  document.querySelectorAll('.editor-toolbar [data-cmd]').forEach(btn => {
    btn.addEventListener('mousedown', e => {
      e.preventDefault();
      const cmd = btn.dataset.cmd;
      editor.focus();
      if (cmd === 'h2') {
        document.execCommand('formatBlock', false, 'h2');
      } else if (cmd === 'h3') {
        document.execCommand('formatBlock', false, 'h3');
      } else if (cmd === 'ul') {
        document.execCommand('insertUnorderedList');
      } else if (cmd === 'ol') {
        document.execCommand('insertOrderedList');
      } else if (cmd === 'quote') {
        document.execCommand('formatBlock', false, 'blockquote');
      } else if (cmd === 'link') {
        const url = prompt('Enter URL:');
        if (url) document.execCommand('createLink', false, url);
      } else {
        document.execCommand(cmd);
      }
    });
  });

  // Placeholder behavior
  if (!editor.innerHTML.trim()) {
    editor.innerHTML = '<p>Start writing your post here…</p>';
    editor.style.color = 'var(--muted)';
    editor.addEventListener('focus', function onFocus() {
      if (editor.innerText.trim() === 'Start writing your post here…') {
        editor.innerHTML = '';
        editor.style.color = 'var(--ink-soft)';
      }
      editor.removeEventListener('focus', onFocus);
    });
  } else {
    editor.style.color = 'var(--ink-soft)';
  }
}

// ── IMAGE UPLOAD PREVIEW ───────────────────────────────
const coverInput = document.getElementById('cover-input');
const coverPreview = document.getElementById('cover-preview');
const uploadZone = document.getElementById('upload-zone');

if (coverInput && coverPreview) {
  coverInput.addEventListener('change', () => {
    const file = coverInput.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = e => {
        coverPreview.src = e.target.result;
        coverPreview.style.display = 'block';
        uploadZone.querySelector('.upload-label').style.display = 'none';
      };
      reader.readAsDataURL(file);
    }
  });
}

// ── NAV SCROLL SHADOW ──────────────────────────────────
const navbar = document.querySelector('.navbar');
if (navbar) {
  window.addEventListener('scroll', () => {
    navbar.style.boxShadow = window.scrollY > 8
      ? '0 2px 20px rgba(0,0,0,.12)'
      : 'none';
  });
}

// ── POST CARD HOVER LIFT ───────────────────────────────
document.querySelectorAll('.post-card').forEach(card => {
  card.addEventListener('mouseenter', () => card.style.willChange = 'transform');
  card.addEventListener('mouseleave', () => card.style.willChange = 'auto');
});

// ── TABLE ROW CLICK TO EDIT ────────────────────────────
document.querySelectorAll('.posts-table tbody tr').forEach(row => {
  row.style.cursor = 'pointer';
  row.addEventListener('click', e => {
    if (e.target.closest('.td-actions')) return;
    const editLink = row.querySelector('a[href*="/edit"]');
    if (editLink) window.location = editLink.href;
  });
});
