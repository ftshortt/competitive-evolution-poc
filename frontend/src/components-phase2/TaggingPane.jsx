import React, { useState, useEffect } from 'react';

const TaggingPane = () => {
  const [tags, setTags] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [selectedTag, setSelectedTag] = useState(null);

  // Fetch existing tags from Neo4j
  useEffect(() => {
    fetchTags();
  }, []);

  const fetchTags = async () => {
    try {
      const response = await fetch('/api/phase2/tags');
      if (response.ok) {
        const data = await response.json();
        setTags(data.tags || []);
      }
    } catch (error) {
      console.error('Error fetching tags:', error);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!inputValue.trim()) return;

    try {
      const response = await fetch('/api/phase2/tag', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ tag: inputValue.trim() }),
      });

      if (response.ok) {
        setInputValue('');
        fetchTags(); // Refresh tag list
      }
    } catch (error) {
      console.error('Error submitting tag:', error);
    }
  };

  const handleTagClick = (tag) => {
    setSelectedTag(selectedTag === tag ? null : tag);
    // Emit event or callback for filtering
    if (typeof window !== 'undefined') {
      window.dispatchEvent(
        new CustomEvent('tagFilter', { detail: { tag: selectedTag === tag ? null : tag } })
      );
    }
  };

  const getTagColor = (index) => {
    const colors = [
      '#3b82f6', // blue
      '#10b981', // green
      '#f59e0b', // amber
      '#ef4444', // red
      '#8b5cf6', // purple
      '#ec4899', // pink
      '#14b8a6', // teal
      '#f97316', // orange
    ];
    return colors[index % colors.length];
  };

  return (
    <div style={styles.container}>
      <h3 style={styles.title}>Knowledge Tags</h3>
      
      <form onSubmit={handleSubmit} style={styles.form}>
        <input
          type="text"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          placeholder="Enter a tag..."
          style={styles.input}
        />
        <button type="submit" style={styles.submitButton}>
          Add Tag
        </button>
      </form>

      <div style={styles.tagCloud}>
        {tags.length === 0 ? (
          <p style={styles.emptyMessage}>No tags yet. Add your first tag!</p>
        ) : (
          tags.map((tag, index) => (
            <span
              key={`${tag}-${index}`}
              onClick={() => handleTagClick(tag)}
              style={{
                ...styles.tagBadge,
                backgroundColor: getTagColor(index),
                opacity: selectedTag && selectedTag !== tag ? 0.5 : 1,
                transform: selectedTag === tag ? 'scale(1.1)' : 'scale(1)',
              }}
            >
              {tag}
            </span>
          ))
        )}
      </div>

      {selectedTag && (
        <div style={styles.filterIndicator}>
          Filtering by: <strong>{selectedTag}</strong>
          <button
            onClick={() => handleTagClick(selectedTag)}
            style={styles.clearButton}
          >
            Clear
          </button>
        </div>
      )}
    </div>
  );
};

const styles = {
  container: {
    padding: '20px',
    backgroundColor: '#f9fafb',
    borderRadius: '8px',
    boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
  },
  title: {
    margin: '0 0 16px 0',
    fontSize: '18px',
    fontWeight: '600',
    color: '#111827',
  },
  form: {
    display: 'flex',
    gap: '8px',
    marginBottom: '20px',
  },
  input: {
    flex: 1,
    padding: '8px 12px',
    border: '1px solid #d1d5db',
    borderRadius: '6px',
    fontSize: '14px',
    outline: 'none',
  },
  submitButton: {
    padding: '8px 16px',
    backgroundColor: '#3b82f6',
    color: 'white',
    border: 'none',
    borderRadius: '6px',
    fontSize: '14px',
    fontWeight: '500',
    cursor: 'pointer',
    transition: 'background-color 0.2s',
  },
  tagCloud: {
    display: 'flex',
    flexWrap: 'wrap',
    gap: '8px',
    minHeight: '60px',
    alignItems: 'flex-start',
  },
  tagBadge: {
    padding: '6px 12px',
    borderRadius: '16px',
    color: 'white',
    fontSize: '13px',
    fontWeight: '500',
    cursor: 'pointer',
    transition: 'all 0.2s',
    userSelect: 'none',
  },
  emptyMessage: {
    color: '#6b7280',
    fontSize: '14px',
    fontStyle: 'italic',
    margin: 0,
  },
  filterIndicator: {
    marginTop: '16px',
    padding: '10px',
    backgroundColor: '#dbeafe',
    borderRadius: '6px',
    fontSize: '14px',
    color: '#1e40af',
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
  },
  clearButton: {
    padding: '4px 8px',
    backgroundColor: '#3b82f6',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    fontSize: '12px',
    cursor: 'pointer',
    marginLeft: 'auto',
  },
};

export default TaggingPane;
