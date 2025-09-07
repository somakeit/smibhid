// Common header and footer functionality
async function loadHeader(subtitle = '') {
    try {
        const response = await fetch('/includes/header.html');
        const headerHTML = await response.text();
        
        // Find the header placeholder and replace it
        const headerPlaceholder = document.getElementById('header-placeholder');
        if (headerPlaceholder) {
            headerPlaceholder.innerHTML = headerHTML;
            
            // Set the page-specific subtitle
            const subtitleElement = document.getElementById('page-subtitle');
            if (subtitleElement && subtitle) {
                subtitleElement.textContent = subtitle;
            }
        }
    } catch (error) {
        console.error('Error loading header:', error);
        // Fallback: create a basic header if loading fails
        const headerPlaceholder = document.getElementById('header-placeholder');
        if (headerPlaceholder) {
            headerPlaceholder.innerHTML = `
                <header class="header">
                    <div class="logo-section">
                        <img src="https://raw.githubusercontent.com/somakeit/smibhid/ba3b3251bfdbf9c8334227aebc1c1a55e858a23f/images/smibhid_logo.png" alt="SMIBHID Logo" class="logo">
                        <h1 class="title">SMIBHID</h1>
                    </div>
                    <div class="subtitle">${subtitle}</div>
                </header>
            `;
        }
    }
}

async function loadFooter(context = '') {
    try {
        const response = await fetch('/includes/footer.html');
        const footerHTML = await response.text();
        
        // Find the footer placeholder and replace it
        const footerPlaceholder = document.getElementById('footer-placeholder');
        if (footerPlaceholder) {
            footerPlaceholder.innerHTML = footerHTML;
            
            // Set the page-specific context
            const contextElement = document.getElementById('footer-context');
            if (contextElement && context) {
                contextElement.textContent = context;
            }
        }
    } catch (error) {
        console.error('Error loading footer:', error);
        // Fallback: create a basic footer if loading fails
        const footerPlaceholder = document.getElementById('footer-placeholder');
        if (footerPlaceholder) {
            footerPlaceholder.innerHTML = `
                <footer class="footer">
                    <p>&copy; 2025 So Make It - SMIBHID ${context}</p>
                </footer>
            `;
        }
    }
}

// Load header and footer when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Check if there's a data-subtitle attribute on the body
    const subtitle = document.body.getAttribute('data-subtitle') || '';
    const footerContext = document.body.getAttribute('data-footer-context') || '';
    
    loadHeader(subtitle);
    loadFooter(footerContext);
});
