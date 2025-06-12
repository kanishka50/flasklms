// Profile page functionality
document.addEventListener('DOMContentLoaded', async function() {
    // Check authentication
    if (!authApi.isLoggedIn() || authApi.getUserRole() !== 'student') {
        window.location.href = '/login.html';
        return;
    }

    // Load profile data
    await loadProfile();

    // Set up form submission
    const profileForm = document.getElementById('profileForm');
    if (profileForm) {
        profileForm.addEventListener('submit', handleProfileUpdate);
    }
});

async function loadProfile() {
    try {
        showLoading();
        const response = await studentApi.getProfile();
        
        if (response.status === 'success' && response.data) {
            populateProfileForm(response.data);
        }
    } catch (error) {
        showError('Failed to load profile');
    } finally {
        hideLoading();
    }
}

function populateProfileForm(data) {
    // User info
    document.getElementById('username').value = data.user.username || '';
    document.getElementById('email').value = data.user.email || '';
    
    // Student info
    document.getElementById('studentId').value = data.student.student_id || '';
    document.getElementById('firstName').value = data.student.first_name || '';
    document.getElementById('lastName').value = data.student.last_name || '';
    document.getElementById('dateOfBirth').value = data.student.date_of_birth || '';
    document.getElementById('gender').value = data.student.gender || '';
    document.getElementById('program').value = data.student.program_code || '';
    document.getElementById('yearOfStudy').value = data.student.year_of_study || '';
    
    // Display-only fields
    document.getElementById('gpa').textContent = data.student.gpa || 'N/A';
    document.getElementById('status').textContent = data.student.status || 'N/A';
    document.getElementById('enrollmentDate').textContent = 
        data.student.enrollment_date ? new Date(data.student.enrollment_date).toLocaleDateString() : 'N/A';
}

async function handleProfileUpdate(e) {
    e.preventDefault();
    
    const formData = {
        email: document.getElementById('email').value,
        first_name: document.getElementById('firstName').value,
        last_name: document.getElementById('lastName').value,
        date_of_birth: document.getElementById('dateOfBirth').value,
        gender: document.getElementById('gender').value
    };
    
    try {
        showLoading();
        const response = await studentApi.updateProfile(formData);
        
        if (response.status === 'success') {
            showSuccess('Profile updated successfully');
            // Reload profile to show updated data
            await loadProfile();
        }
    } catch (error) {
        showError('Failed to update profile');
    } finally {
        hideLoading();
    }
}