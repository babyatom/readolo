// A reusable function to inject HTML into a specific element
async function injectComponent(elementId, filePath) {
    try {
        const response = await fetch(filePath);
        if (!response.ok) throw new Error(`Could not find ${filePath}`);
        const html = await response.text();
        document.getElementById(elementId).innerHTML = html;
    } catch (error) {
        console.error("Error loading component:", error);
    }
}

// Insert email safely (bot-resistant)
function injectEmail() {
    const emailEl = document.getElementById("email");
    if (!emailEl) return;

    const user = "hello";
    const domain = "readolo.com";
    emailEl.textContent = `${user}@${domain}`;
}

// Run this when the page loads
window.addEventListener('DOMContentLoaded', async () => {
    await injectComponent('nav-placeholder', '/components/nav.html');
    await injectComponent('footer-placeholder', '/components/footer.html');

    // Run AFTER components load
    injectEmail();

    // Subtle reveal animations on scroll
    const revealEls = document.querySelectorAll('.reveal');
    if (revealEls.length > 0 && 'IntersectionObserver' in window) {
        const observer = new IntersectionObserver(
            (entries) => {
                entries.forEach((entry) => {
                    if (entry.isIntersecting) {
                        entry.target.classList.add('in-view');
                        observer.unobserve(entry.target);
                    }
                });
            },
            { threshold: 0.15 }
        );

        revealEls.forEach((el, index) => {
            if (index % 3 === 1) el.classList.add('reveal-delay-1');
            if (index % 3 === 2) el.classList.add('reveal-delay-2');
            observer.observe(el);
        });
    } else {
        revealEls.forEach((el) => el.classList.add('in-view'));
    }

    // Contact form AJAX submission (Formspree)
    const contactForm = document.getElementById('contact-form');
    const formStatus = document.getElementById('form-status');
    if (contactForm && formStatus) {
        contactForm.addEventListener('submit', async (event) => {
            event.preventDefault();
            formStatus.textContent = 'Sending...';
            formStatus.style.color = '#555';

            try {
                const formData = new FormData(contactForm);
                const response = await fetch(contactForm.action, {
                    method: 'POST',
                    body: formData,
                    headers: {
                        'Accept': 'application/json'
                    }
                });

                if (response.ok) {
                    window.location.href = '/thank-you.html';
                } else {
                    formStatus.textContent = 'Something went wrong. Please try again or email hello@readolo.com.';
                    formStatus.style.color = '#CC0000';
                }
            } catch (error) {
                formStatus.textContent = 'Network error. Please try again or email hello@readolo.com.';
                formStatus.style.color = '#CC0000';
            }
        });
    }
});
