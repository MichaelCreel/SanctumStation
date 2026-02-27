(function() {
    'use strict';
    
    let currentNote = 'Untitled Note';
    let autoSaveTimeout = null;
    let isSaving = false;
    
    const editor = document.getElementById('editor');
    const titleInput = document.getElementById('noteTitle');
    const saveIndicator = document.getElementById('saveIndicator');
    
    // Initialize
    function init() {
        // Set up event listeners
        editor.addEventListener('input', handleEditorInput);
        titleInput.addEventListener('input', handleTitleInput);
        
        // Handle keyboard shortcuts
        editor.addEventListener('keydown', handleKeyboardShortcuts);
        
        // Load a default note or create new
        newNote();
    }
    
    // Handle editor input with auto-save
    function handleEditorInput() {
        clearTimeout(autoSaveTimeout);
        autoSaveTimeout = setTimeout(() => {
            saveNote(false); // Auto-save without showing indicator
        }, 2000); // Save after 2 seconds of no typing
    }
    
    // Handle title input
    function handleTitleInput() {
        currentNote = titleInput.value.trim() || 'Untitled Note';
        clearTimeout(autoSaveTimeout);
        autoSaveTimeout = setTimeout(() => {
            saveNote(false);
        }, 2000);
    }
    
    // Handle keyboard shortcuts
    function handleKeyboardShortcuts(e) {
        if (e.ctrlKey || e.metaKey) {
            switch(e.key.toLowerCase()) {
                case 'b':
                    e.preventDefault();
                    formatText('bold');
                    break;
                case 'i':
                    e.preventDefault();
                    formatText('italic');
                    break;
                case 'u':
                    e.preventDefault();
                    formatText('underline');
                    break;
                case 's':
                    e.preventDefault();
                    saveNote(true);
                    break;
            }
        }
    }
    
    // Format text
    window.formatText = function(command) {
        document.execCommand(command, false, null);
        editor.focus();
    };
    
    // Format heading
    window.formatHeading = function(level) {
        document.execCommand('formatBlock', false, `<h${level}>`);
        editor.focus();
    };
    
    // Insert link
    window.insertLink = function() {
        const url = prompt('Enter URL:');
        if (url) {
            document.execCommand('createLink', false, url);
        }
        editor.focus();
    };
    
    // Insert code block
    window.insertCode = function() {
        const code = prompt('Enter code:');
        if (code) {
            const codeElement = document.createElement('code');
            codeElement.textContent = code;
            insertNodeAtCursor(codeElement);
        }
        editor.focus();
    };
    
    // Helper to insert node at cursor
    function insertNodeAtCursor(node) {
        const selection = window.getSelection();
        if (selection.rangeCount > 0) {
            const range = selection.getRangeAt(0);
            range.deleteContents();
            range.insertNode(node);
            range.setStartAfter(node);
            range.setEndAfter(node);
            selection.removeAllRanges();
            selection.addRange(range);
        }
    }
    
    // Convert HTML to Markdown
    function htmlToMarkdown(html) {
        let markdown = html;
        
        // Clean up HTML
        markdown = markdown.replace(/<br\s*\/?>/gi, '\n');
        
        // Headers
        markdown = markdown.replace(/<h1[^>]*>(.*?)<\/h1>/gi, '# $1\n\n');
        markdown = markdown.replace(/<h2[^>]*>(.*?)<\/h2>/gi, '## $1\n\n');
        markdown = markdown.replace(/<h3[^>]*>(.*?)<\/h3>/gi, '### $1\n\n');
        markdown = markdown.replace(/<h4[^>]*>(.*?)<\/h4>/gi, '#### $1\n\n');
        markdown = markdown.replace(/<h5[^>]*>(.*?)<\/h5>/gi, '##### $1\n\n');
        markdown = markdown.replace(/<h6[^>]*>(.*?)<\/h6>/gi, '###### $1\n\n');
        
        // Bold and italic
        markdown = markdown.replace(/<strong[^>]*>(.*?)<\/strong>/gi, '**$1**');
        markdown = markdown.replace(/<b[^>]*>(.*?)<\/b>/gi, '**$1**');
        markdown = markdown.replace(/<em[^>]*>(.*?)<\/em>/gi, '*$1*');
        markdown = markdown.replace(/<i[^>]*>(.*?)<\/i>/gi, '*$1*');
        
        // Strikethrough
        markdown = markdown.replace(/<strike[^>]*>(.*?)<\/strike>/gi, '~~$1~~');
        markdown = markdown.replace(/<s[^>]*>(.*?)<\/s>/gi, '~~$1~~');
        markdown = markdown.replace(/<del[^>]*>(.*?)<\/del>/gi, '~~$1~~');
        
        // Underline (not standard markdown, using HTML)
        markdown = markdown.replace(/<u[^>]*>(.*?)<\/u>/gi, '<u>$1</u>');
        
        // Links
        markdown = markdown.replace(/<a[^>]*href="([^"]*)"[^>]*>(.*?)<\/a>/gi, '[$2]($1)');
        
        // Code
        markdown = markdown.replace(/<code[^>]*>(.*?)<\/code>/gi, '`$1`');
        markdown = markdown.replace(/<pre[^>]*><code[^>]*>(.*?)<\/code><\/pre>/gi, '```\n$1\n```');
        
        // Lists
        markdown = markdown.replace(/<ul[^>]*>(.*?)<\/ul>/gis, (match, content) => {
            return content.replace(/<li[^>]*>(.*?)<\/li>/gi, '- $1\n');
        });
        markdown = markdown.replace(/<ol[^>]*>(.*?)<\/ol>/gis, (match, content) => {
            let index = 1;
            return content.replace(/<li[^>]*>(.*?)<\/li>/gi, () => `${index++}. $1\n`);
        });
        
        // Paragraphs
        markdown = markdown.replace(/<p[^>]*>(.*?)<\/p>/gi, '$1\n\n');
        markdown = markdown.replace(/<div[^>]*>(.*?)<\/div>/gi, '$1\n');
        
        // Remove remaining HTML tags
        markdown = markdown.replace(/<[^>]*>/g, '');
        
        // Clean up entities
        markdown = markdown.replace(/&nbsp;/g, ' ');
        markdown = markdown.replace(/&amp;/g, '&');
        markdown = markdown.replace(/&lt;/g, '<');
        markdown = markdown.replace(/&gt;/g, '>');
        markdown = markdown.replace(/&quot;/g, '"');
        
        // Clean up excessive newlines
        markdown = markdown.replace(/\n{3,}/g, '\n\n');
        markdown = markdown.trim();
        
        return markdown;
    }
    
    // Convert Markdown to HTML (simple implementation)
    function markdownToHtml(markdown) {
        let html = markdown;
        
        // Escape HTML first
        html = html.replace(/&/g, '&amp;')
                   .replace(/</g, '&lt;')
                   .replace(/>/g, '&gt;');
        
        // Code blocks (before other processing)
        html = html.replace(/```(.*?)```/gs, '<pre><code>$1</code></pre>');
        
        // Headers
        html = html.replace(/^######\s+(.+)$/gm, '<h6>$1</h6>');
        html = html.replace(/^#####\s+(.+)$/gm, '<h5>$1</h5>');
        html = html.replace(/^####\s+(.+)$/gm, '<h4>$1</h4>');
        html = html.replace(/^###\s+(.+)$/gm, '<h3>$1</h3>');
        html = html.replace(/^##\s+(.+)$/gm, '<h2>$1</h2>');
        html = html.replace(/^#\s+(.+)$/gm, '<h1>$1</h1>');
        
        // Bold and italic
        html = html.replace(/\*\*\*(.+?)\*\*\*/g, '<strong><em>$1</em></strong>');
        html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
        html = html.replace(/\*(.+?)\*/g, '<em>$1</em>');
        html = html.replace(/___(.+?)___/g, '<strong><em>$1</em></strong>');
        html = html.replace(/__(.+?)__/g, '<strong>$1</strong>');
        html = html.replace(/_(.+?)_/g, '<em>$1</em>');
        
        // Strikethrough
        html = html.replace(/~~(.+?)~~/g, '<s>$1</s>');
        
        // Inline code
        html = html.replace(/`(.+?)`/g, '<code>$1</code>');
        
        // Links
        html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2">$1</a>');
        
        // Unordered lists
        html = html.replace(/^\s*[-*+]\s+(.+)$/gm, '<li>$1</li>');
        html = html.replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>');
        
        // Ordered lists
        html = html.replace(/^\s*\d+\.\s+(.+)$/gm, '<li>$1</li>');
        
        // Paragraphs
        const lines = html.split('\n');
        let inList = false;
        let result = [];
        
        for (let i = 0; i < lines.length; i++) {
            const line = lines[i].trim();
            
            if (line.startsWith('<h') || line.startsWith('<ul') || 
                line.startsWith('</ul') || line.startsWith('<pre') || 
                line.startsWith('</pre') || line === '') {
                result.push(line);
            } else if (line.startsWith('<li>')) {
                if (!inList) {
                    result.push('<ul>');
                    inList = true;
                }
                result.push(line);
            } else {
                if (inList) {
                    result.push('</ul>');
                    inList = false;
                }
                if (line) {
                    result.push('<p>' + line + '</p>');
                }
            }
        }
        
        if (inList) {
            result.push('</ul>');
        }
        
        return result.join('\n');
    }
    
    // Save note
    window.saveNote = async function(showIndicator = true) {
        if (isSaving) return;
        isSaving = true;
        
        const title = titleInput.value.trim() || 'Untitled Note';
        const htmlContent = editor.innerHTML;
        const markdownContent = htmlToMarkdown(htmlContent);
        
        if (showIndicator) {
            showSaveIndicator('Saving...', 'saving');
        }
        
        try {
            const result = await window.pywebview.api.call_app_function('Notes', 'save_note', title, markdownContent);
            
            if (result.success) {
                currentNote = title;
                if (showIndicator) {
                    showSaveIndicator('Saved!', 'success');
                }
            } else {
                if (showIndicator) {
                    showSaveIndicator('Error: ' + (result.error || 'Failed to save'), 'error');
                }
            }
        } catch (error) {
            console.error('Error saving note:', error);
            if (showIndicator) {
                showSaveIndicator('Error saving note', 'error');
            }
        }
        
        isSaving = false;
    };
    
    // Load note
    window.loadNote = async function(title) {
        try {
            const result = await window.pywebview.api.call_app_function('Notes', 'load_note', title);
            
            if (result.success) {
                titleInput.value = title;
                currentNote = title;
                
                // Convert markdown to HTML and set editor content
                const htmlContent = markdownToHtml(result.content);
                editor.innerHTML = htmlContent;
                
                closeLoadModal();
                showSaveIndicator('Loaded: ' + title, 'success');
            } else {
                showSaveIndicator('Error: ' + (result.error || 'Failed to load'), 'error');
            }
        } catch (error) {
            console.error('Error loading note:', error);
            showSaveIndicator('Error loading note', 'error');
        }
    };
    
    // Delete note
    window.deleteNote = async function(title, event) {
        event.stopPropagation();
        
        if (!confirm(`Delete note "${title}"?`)) {
            return;
        }
        
        try {
            const result = await window.pywebview.api.call_app_function('Notes', 'delete_note', title);
            
            if (result.success) {
                showSaveIndicator('Deleted: ' + title, 'success');
                showLoadModal(); // Refresh the list
            } else {
                showSaveIndicator('Error: ' + (result.error || 'Failed to delete'), 'error');
            }
        } catch (error) {
            console.error('Error deleting note:', error);
            showSaveIndicator('Error deleting note', 'error');
        }
    };
    
    // New note
    window.newNote = function() {
        titleInput.value = 'Untitled Note';
        currentNote = 'Untitled Note';
        editor.innerHTML = '<p>Start typing your note...</p>';
        editor.focus();
    };
    
    // Show load modal
    window.showLoadModal = async function() {
        const modal = document.getElementById('loadModal');
        const notesList = document.getElementById('notesList');
        
        modal.classList.add('active');
        
        try {
            const result = await window.pywebview.api.call_app_function('Notes', 'list_notes');
            
            if (result.success && result.notes.length > 0) {
                notesList.innerHTML = result.notes.map(note => `
                    <div class="note-item" onclick="window.loadNote('${note}')">
                        <span class="note-item-title">${note}</span>
                        <button class="note-item-delete" onclick="window.deleteNote('${note}', event)">Delete</button>
                    </div>
                `).join('');
            } else {
                notesList.innerHTML = '<p class="no-notes">No notes found</p>';
            }
        } catch (error) {
            console.error('Error listing notes:', error);
            notesList.innerHTML = '<p class="no-notes">Error loading notes</p>';
        }
    };
    
    // Close load modal
    window.closeLoadModal = function() {
        const modal = document.getElementById('loadModal');
        modal.classList.remove('active');
    };
    
    // Show save indicator
    function showSaveIndicator(message, type = 'success') {
        saveIndicator.textContent = message;
        saveIndicator.className = 'save-indicator show';
        
        if (type === 'saving') {
            saveIndicator.classList.add('saving');
        } else if (type === 'error') {
            saveIndicator.classList.add('error');
        }
        
        setTimeout(() => {
            saveIndicator.classList.remove('show');
        }, 3000);
    }
    
    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
