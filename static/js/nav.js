document.addEventListener('DOMContentLoaded', function() {
    const toggle = document.getElementById('navToggle');
    const links = document.getElementById('navLinks');
    if (!toggle || !links) return;

    toggle.addEventListener('click', function() {
        const isOpen = links.classList.toggle('open');
        toggle.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
    });

    links.querySelectorAll('a').forEach(a => {
        a.addEventListener('click', () => links.classList.remove('open'));
    });
});
