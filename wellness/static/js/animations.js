document.addEventListener("DOMContentLoaded", () => {
    // 1. Intersection Observer for fade-in animations
    const observerOptions = {
        root: null,
        rootMargin: '0px',
        threshold: 0.15
    };

    const fadeObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
                // Optional: Stop observing once faded in if you only want it to happen once
                // observer.unobserve(entry.target); 
            }
        });
    }, observerOptions);

    // Grab elements we want to animate. We attach fade-in to major cards and sections.
    const elementsToAnimate = document.querySelectorAll(
        '.fade-in, .resource-card, .action-card, .question-group, .form-container, .chat-container, .assessment-container'
    );
    
    elementsToAnimate.forEach((el) => {
        el.classList.add('has-fade-animation'); // Prepare them for CSS targeting
        fadeObserver.observe(el);
    });

    // 2. Animated Sticky Navbar – enhanced drop shadow on scroll
    const topnav = document.querySelector('.topnav');

    window.addEventListener('scroll', () => {
        if (window.scrollY > 15) {
            if (topnav) topnav.classList.add('scrolled-nav');
        } else {
            if (topnav) topnav.classList.remove('scrolled-nav');
        }
    });
});
