// Auth Guard Utility
document.addEventListener('DOMContentLoaded', function() {
    // Check if user is logged in
    if (!authApi.isLoggedIn()) {
        // Redirect to login page
        window.location.href = '/index.html';
        return;
    }
    
    // Get current page type
    const currentPath = window.location.pathname;
    
    // Check if user has access to this page
    if (currentPath.includes('/student/') && !authApi.hasRole('student')) {
        // Redirect to appropriate dashboard
        redirectToDashboard();
        return;
    }
    
    if (currentPath.includes('/faculty/') && !authApi.hasRole('faculty')) {
        // Redirect to appropriate dashboard
        redirectToDashboard();
        return;
    }
    
    if (currentPath.includes('/admin/') && !authApi.hasRole('admin')) {
        // Redirect to appropriate dashboard
        redirectToDashboard();
        return;
    }
    
    // User is authorized to view this page
    console.log('User authorized to view this page');
    
    // Function to redirect to appropriate dashboard
    function redirectToDashboard() {
        const userType = authApi.getUserRole();
        
        if (userType === 'student') {
            window.location.href = '/student/dashboard.html';
        } else if (userType === 'faculty') {
            window.location.href = '/faculty/dashboard.html';
        } else if (userType === 'admin') {
            window.location.href = '/admin/dashboard.html';
        } else {
            window.location.href = '/index.html';
        }
    }
});