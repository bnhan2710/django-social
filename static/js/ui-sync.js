/**
 * UI Synchronization JavaScript
 * Handles theme switching, dropdown positioning, and responsive design fixes
 */

document.addEventListener('DOMContentLoaded', function() {
    // =========================
    // Theme Management
    // =========================
    const themeSwitch = document.getElementById('themeSwitch');
    const body = document.body;
    const themeSwitchIcon = themeSwitch ? themeSwitch.querySelector('i') : null;
    
    // Force light mode as default by setting 'light' in localStorage
    localStorage.setItem('theme', 'light');
    
    // Remove dark-mode class if it exists
    body.classList.remove('dark-mode');
    updateThemeIcon();
    
    // Theme switch button event handler
    if (themeSwitch) {
        themeSwitch.addEventListener('click', () => {
            body.classList.toggle('dark-mode');
            updateThemeIcon();
            localStorage.setItem('theme', body.classList.contains('dark-mode') ? 'dark' : 'light');
        });
    }
    
    function updateThemeIcon() {
        if (!themeSwitchIcon) return;
        
        const isDarkMode = body.classList.contains('dark-mode');
        if (isDarkMode) {
            themeSwitchIcon.classList.remove('fa-moon');
            themeSwitchIcon.classList.add('fa-sun');
        } else {
            themeSwitchIcon.classList.remove('fa-sun');
            themeSwitchIcon.classList.add('fa-moon');
        }
    }
    
    // =========================
    // Dropdown Positioning Fixes
    // =========================
    
    // Fix dropdown positioning to prevent them from going off-screen
    function fixDropdownPositioning() {
        document.querySelectorAll('.dropdown').forEach(dropdown => {
            const dropdownMenu = dropdown.querySelector('.dropdown-menu');
            if (!dropdownMenu) return;
            
            // Directly handling MDB dropdown behavior
            dropdown.addEventListener('shown.bs.dropdown', function() {
                const dropdownRect = dropdownMenu.getBoundingClientRect();
                const viewportWidth = window.innerWidth;
                const viewportHeight = window.innerHeight;
                
                // Fix horizontal positioning
                if (dropdownRect.right > viewportWidth) {
                    dropdownMenu.classList.add('dropdown-menu-end');
                }
                
                // Fix vertical positioning
                if (dropdownRect.bottom > viewportHeight) {
                    dropdownMenu.style.top = 'auto';
                    dropdownMenu.style.transform = 'translateY(-100%)';
                    dropdownMenu.style.marginTop = '-4px';
                }
            });
            
            // Reset position when dropdown is hidden
            dropdown.addEventListener('hidden.bs.dropdown', function() {
                dropdownMenu.style.top = '';
                dropdownMenu.style.transform = '';
                dropdownMenu.style.marginTop = '';
            });
        });
    }
    
    // Initialize dropdown fix
    fixDropdownPositioning();
    
    // Update on window resize
    window.addEventListener('resize', () => {
        fixDropdownPositioning();
    });
    
    // =========================
    // Fade-in animations
    // =========================
    
    // Apply fade-in animation to elements with .fade-in class
    setTimeout(() => {
        document.querySelectorAll('.fade-in').forEach((element, index) => {
            setTimeout(() => {
                element.style.opacity = '1';
                element.style.transform = 'translateY(0)';
            }, index * 100);
        });
    }, 300);
    
    // =========================
    // Mobile-specific adjustments
    // =========================
    
    function handleMobileAdjustments() {
        const isMobile = window.innerWidth < 768;
        
        // Handle modal scrolling on mobile
        document.querySelectorAll('.modal').forEach(modal => {
            if (isMobile) {
                modal.style.maxHeight = '100vh';
                modal.style.overflowY = 'auto';
            } else {
                modal.style.maxHeight = '';
                modal.style.overflowY = '';
            }
        });
        
        // Adjust navbar padding on scroll for mobile
        if (isMobile) {
            window.addEventListener('scroll', () => {
                const header = document.querySelector('header');
                if (!header) return;
                
                if (window.scrollY > 10) {
                    header.style.boxShadow = 'var(--box-shadow)';
                    header.querySelector('.navbar').style.padding = '0.5rem 1rem';
                } else {
                    header.style.boxShadow = '';
                    header.querySelector('.navbar').style.padding = '0.7rem 1rem';
                }
            });
        }
    }
    
    // Initialize mobile adjustments
    handleMobileAdjustments();
    
    // Update on window resize
    window.addEventListener('resize', handleMobileAdjustments);
});