document.querySelectorAll('.copy-btn').forEach(button => {
    button.addEventListener('click', () => {
        const formatted = `
Title: ${button.dataset.title}
Source: ${button.dataset.source}
Date: ${button.dataset.date}
Link: ${button.dataset.link}
Summary: ${button.dataset.summary}
`;

        // Copy text
        navigator.clipboard.writeText(formatted).then(() => {
            showNotification();
        });

        // Download image
        if(button.dataset.image){
            const link = document.createElement('a');
            link.href = button.dataset.image;
            link.download = `${button.dataset.title.replace(/\s+/g,'_')}.jpg`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        }
    });
});

// Show "Copied!" notification
function showNotification(){
    const notif = document.getElementById('copy-notification');
    notif.style.opacity = 1;
    setTimeout(() => {
        notif.style.opacity = 0;
    }, 2000);
}
