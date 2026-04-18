document.addEventListener('DOMContentLoaded', () => {
    const searchToggle = document.getElementById('searchToggle');
    const searchInput = document.getElementById('searchInput');
    const searchContainer = document.querySelector('.search-container');
    const blogPosts = document.querySelectorAll('.blog-post');
    if (!searchToggle || !searchInput || !searchContainer) return;

    function filterPosts(query) {
        const term = query.toLowerCase().trim();
        blogPosts.forEach(post => {
            const title = post.querySelector('h3')?.textContent.toLowerCase() || '';
            const preview = post.querySelector('.blog-post-content p')?.textContent.toLowerCase() || '';
            const matches = term === '' || title.includes(term) || preview.includes(term);
            post.style.display = matches ? '' : 'none';
        });
    }

    searchToggle.addEventListener('click', () => {
        searchContainer.classList.toggle('active');
        if (searchContainer.classList.contains('active')) {
            searchInput.focus();
        } else {
            searchInput.value = '';
            filterPosts('');
        }
    });

    searchInput.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            searchContainer.classList.remove('active');
            searchInput.value = '';
            filterPosts('');
        }
    });

    searchInput.addEventListener('input', (e) => filterPosts(e.target.value));
});
