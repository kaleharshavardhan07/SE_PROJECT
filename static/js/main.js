
/* static/js/main.js */
// Global JavaScript functions

// Display loading spinner
function showLoader() {
    const loader = document.createElement('div');
    loader.className = 'position-fixed top-0 start-0 w-100 h-100 d-flex justify-content-center align-items-center bg-white bg-opacity-75';
    loader.style.zIndex = '9999';
    loader.innerHTML = `
        <div class="spinner-border text-primary" role="status">
            <span class="visually-hidden">Loading...</span>
        </div>
    `;
    
    document.body.appendChild(loader);
    return loader;
}

function hideLoader(loader) {
    if (loader) {
        document.body.removeChild(loader);
    }
}

// Format date
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}