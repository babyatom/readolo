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

// Run this when the page loads
window.addEventListener('DOMContentLoaded', () => {
    injectComponent('nav-placeholder', '/components/nav.html');
    injectComponent('footer-placeholder', '/components/footer.html');
});