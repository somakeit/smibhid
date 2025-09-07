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
            
            // Initialize navigation
            initializeNavigation();
        }
    } catch (error) {
        console.error('Error loading header:', error);
        // Fallback: create a basic header if loading fails
        const headerPlaceholder = document.getElementById('header-placeholder');
        if (headerPlaceholder) {
            headerPlaceholder.innerHTML = `
                <header class="header">
                    <div class="header-content">
                        <div class="logo-section">
                            <img src="https://raw.githubusercontent.com/somakeit/smibhid/ba3b3251bfdbf9c8334227aebc1c1a55e858a23f/images/smibhid_logo.png" alt="SMIBHID Logo" class="logo">
                            <div class="title-section">
                                <h1 class="title">SMIBHID</h1>
                                <div class="subtitle">${subtitle}</div>
                            </div>
                        </div>
                    </div>
                </header>
            `;
        }
    }
}

function initializeNavigation() {
    // Mobile menu toggle
    const mobileToggle = document.getElementById('mobile-menu-toggle');
    const navMenu = document.getElementById('nav-menu');
    
    if (mobileToggle && navMenu) {
        mobileToggle.addEventListener('click', () => {
            navMenu.classList.toggle('active');
        });
    }
    
    // Check for sensor availability and update navbar
    checkSensorAvailability();
    
    // Set up periodic refresh for sensor availability (every minute)
    const refreshInterval = setInterval(() => {
        checkSensorAvailability();
    }, 60000); // 60 seconds
    
    // Store interval ID for potential cleanup
    window.sensorRefreshInterval = refreshInterval;
    
    // Highlight active page
    highlightActivePage();
    
    // Handle dropdown clicks on mobile
    const dropdownItems = document.querySelectorAll('.dropdown');
    dropdownItems.forEach(item => {
        const link = item.querySelector('.nav-link');
        if (link) {
            link.addEventListener('click', (e) => {
                if (window.innerWidth <= 768) {
                    e.preventDefault();
                    item.classList.toggle('active');
                }
            });
        }
    });
}

async function checkSensorAvailability() {
    const CACHE_DURATION = 60 * 1000; // 1 minute in milliseconds
    const now = Date.now();
    
    // Check if we have cached data and if it's still valid
    const cachedSensorsAvailable = localStorage.getItem('sensors-available');
    const cachedSCD30Available = localStorage.getItem('scd30-available');
    const cacheTimestamp = localStorage.getItem('sensors-cache-timestamp');
    
    if (cachedSensorsAvailable !== null && cachedSCD30Available !== null && cacheTimestamp !== null) {
        const cacheAge = now - parseInt(cacheTimestamp);
        
        if (cacheAge < CACHE_DURATION) {
            // Cache is still valid, use cached results
            const sensorsAvailable = cachedSensorsAvailable === 'true';
            const scd30Available = cachedSCD30Available === 'true';
            updateSensorNavVisibility(sensorsAvailable, scd30Available);
            console.log(`Using cached sensor availability: sensors=${sensorsAvailable}, scd30=${scd30Available} (cache age: ${Math.round(cacheAge / 1000)}s)`);
            return;
        } else {
            console.log('Sensor cache expired, refreshing...');
        }
    }
    
    try {
        // Fetch the sensors module list to check availability
        const response = await fetch('/api/sensors/modules');
        if (response.ok) {
            const modules = await response.json();
            
            // Check if any sensors are available
            let sensorsAvailable = false;
            let scd30Available = false;
            
            if (Array.isArray(modules)) {
                sensorsAvailable = modules.length > 0;
                scd30Available = modules.includes('SCD30');
            } else if (typeof modules === 'object' && modules !== null) {
                const moduleKeys = Object.keys(modules);
                sensorsAvailable = moduleKeys.length > 0;
                scd30Available = modules.hasOwnProperty('SCD30');
            }
            
            // Cache the results with timestamp
            localStorage.setItem('sensors-available', sensorsAvailable.toString());
            localStorage.setItem('scd30-available', scd30Available.toString());
            localStorage.setItem('sensors-cache-timestamp', now.toString());
            
            console.log(`Sensor availability updated: sensors=${sensorsAvailable}, scd30=${scd30Available}`);
            updateSensorNavVisibility(sensorsAvailable, scd30Available);
        } else {
            console.warn('Could not fetch sensor modules list, keeping sensor nav items visible');
            // Default to visible if we can't check, but don't cache this failure
            updateSensorNavVisibility(true, true);
        }
    } catch (error) {
        console.warn('Error checking sensor availability:', error);
        // Default to visible if there's an error, but don't cache this failure
        updateSensorNavVisibility(true, true);
    }
}

function updateSensorNavVisibility(sensorsAvailable, scd30Available) {
    // Update the main Sensors dropdown visibility
    const sensorsDropdown = document.querySelector('#nav-sensors');
    if (sensorsDropdown) {
        if (sensorsAvailable) {
            sensorsDropdown.style.display = '';
        } else {
            sensorsDropdown.style.display = 'none';
            console.log('No sensor modules detected, hiding entire Sensors nav section');
        }
    }
    
    // Update the SCD30 link visibility within the sensors dropdown
    const scd30NavLink = document.getElementById('scd30-nav-link');
    if (scd30NavLink) {
        const parentLi = scd30NavLink.closest('li');
        if (parentLi) {
            if (scd30Available) {
                parentLi.style.display = 'block';
            } else {
                parentLi.style.display = 'none';
                console.log('SCD30 module not detected, hiding SCD30 nav option');
            }
        }
    }
}

// Utility function to manually clear sensor cache (useful for debugging)
function clearSensorCache() {
    localStorage.removeItem('sensors-available');
    localStorage.removeItem('scd30-available');
    localStorage.removeItem('sensors-cache-timestamp');
    console.log('Sensor cache cleared');
}

// Make cache clearing function available globally for debugging
window.clearSensorCache = clearSensorCache;

function highlightActivePage() {
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.nav-link');
    
    navLinks.forEach(link => {
        link.classList.remove('active');
        
        const linkPath = new URL(link.href).pathname;
        
        // Handle exact matches and special cases
        if (currentPath === linkPath ||
            (currentPath === '/' && linkPath === '/') ||
            (currentPath.startsWith('/sensors') && linkPath === '/sensors') ||
            (currentPath === '/api' && linkPath === '/api') ||
            (currentPath === '/update' && linkPath === '/update')) {
            link.classList.add('active');
        }
    });
    
    // Special handling for SCD30 dropdown link
    const scd30Link = document.getElementById('scd30-nav-link');
    if (scd30Link && (currentPath === '/sensors/scd30' || currentPath === '/sensors/scd30.html')) {
        scd30Link.classList.add('active');
        // Also highlight the parent sensors link
        const sensorsLink = document.querySelector('[data-page="sensors"]');
        if (sensorsLink) {
            sensorsLink.classList.add('active');
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
