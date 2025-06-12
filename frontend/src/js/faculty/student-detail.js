// student-detail.js - Individual Student Detail Page
document.addEventListener('DOMContentLoaded', function() {
    // Initialize page
    initializePage();
    
    // Get student ID from URL
    const urlParams = new URLSearchParams(window.location.search);
    const studentId = urlParams.get('id');
    
    if (studentId) {
        loadStudentDetail(studentId);
    } else {
        showError('Student ID not provided');
    }
});

// Page Elements
let studentData = null;
let attendanceChart = null;
let gradeChart = null;

function initializePage() {
    // Initialize tabs
    initializeTabs();
    
    // Initialize logout button
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', logout);
    }
    
    // Initialize back button
    const backBtn = document.querySelector('.btn-secondary');
    if (backBtn) {
        backBtn.addEventListener('click', () => {
            window.history.back();
        });
    }
    
    // Initialize action buttons
    initializeActionButtons();
}

function initializeTabs() {
    const tabButtons = document.querySelectorAll('.nav-link');
    const tabPanes = document.querySelectorAll('.tab-pane');
    
    tabButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Remove active class from all tabs
            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabPanes.forEach(pane => pane.classList.remove('show', 'active'));
            
            // Add active class to clicked tab
            this.classList.add('active');
            
            // Show corresponding pane
            const targetId = this.getAttribute('href').substring(1);
            const targetPane = document.getElementById(targetId);
            if (targetPane) {
                targetPane.classList.add('show', 'active');
                
                // Load specific tab content
                handleTabChange(targetId);
            }
        });
    });
}

function initializeActionButtons() {
    // Send alert button
    const sendAlertBtn = document.getElementById('sendAlertBtn');
    if (sendAlertBtn) {
        sendAlertBtn.addEventListener('click', showSendAlertModal);
    }
    
    // Schedule meeting button
    const scheduleMeetingBtn = document.getElementById('scheduleMeetingBtn');
    if (scheduleMeetingBtn) {
        scheduleMeetingBtn.addEventListener('click', showScheduleMeetingModal);
    }
    
    // Add note button
    const addNoteBtn = document.getElementById('addNoteBtn');
    if (addNoteBtn) {
        addNoteBtn.addEventListener('click', showAddNoteModal);
    }
}

async function loadStudentDetail(studentId) {
    try {
        showLoading();
        
        // Load student data using the API client
        const response = await apiClient.get(`faculty/students/${studentId}`);
        
        if (response.status === 'success') {
            studentData = response.data.student;
            populateStudentInfo(studentData);
            loadAttendanceData(studentId);
            loadGradeData(studentId);
            loadInterventions(studentId);
        } else {
            throw new Error(response.message || 'Failed to load student data');
        }
        
    } catch (error) {
        console.error('Error loading student detail:', error);
        showError('Failed to load student information');
    } finally {
        hideLoading();
    }
}

function populateStudentInfo(student) {
    
    // Update page title
    document.title = `${student.name} - Student Detail`;
    
    // Update breadcrumb
    const breadcrumbName = document.getElementById('breadcrumbName');
    if (breadcrumbName) {
        breadcrumbName.textContent = student.name;
    }
    
    // Student header info
    const studentName = document.getElementById('studentName');
    const studentId = document.getElementById('studentId');
    const courseInfo = document.getElementById('courseInfo');
    const studentInitials = document.getElementById('studentInitials');
    
    if (studentName) studentName.textContent = student.name;
    if (studentId) studentId.textContent = `ID: ${student.student_id}`;
    if (courseInfo) courseInfo.textContent = `${student.course_code} - ${student.course_name}`;
    if (studentInitials) {
        studentInitials.textContent = getInitials(student.name);
    }
    
    // Risk badge
    const riskContainer = document.getElementById('riskBadgeContainer');
    if (riskContainer) {
        const riskColor = getRiskColor(student.risk_level);
        riskContainer.innerHTML = `
            <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-${riskColor}-100 text-${riskColor}-800">
                ${capitalizeFirst(student.risk_level)} Risk
            </span>
        `;
    }
    
    // Performance cards
    const currentGPA = document.getElementById('currentGPA');
    const attendanceRate = document.getElementById('attendanceRate');
    const predictedGrade = document.getElementById('predictedGrade');
    const riskLevel = document.getElementById('riskLevel');
    
    if (currentGPA) currentGPA.textContent = student.overall_gpa || 'N/A';
    if (attendanceRate) attendanceRate.textContent = `${student.attendance_rate || 0}%`;
    if (predictedGrade) predictedGrade.textContent = student.predicted_grade || student.current_grade || 'N/A';
    if (riskLevel) riskLevel.textContent = capitalizeFirst(student.risk_level);
}

function getInitials(name) {
    if (!name) return 'XX';
    return name.split(' ').map(n => n[0]).join('').toUpperCase().substring(0, 2);
}

function capitalizeFirst(str) {
    if (!str) return '';
    return str.charAt(0).toUpperCase() + str.slice(1);
}

function populateCurrentCourses(courses) {
    const container = document.getElementById('currentCourses');
    if (!container) return;
    
    if (courses.length === 0) {
        container.innerHTML = '<p class="text-muted">No current enrollments</p>';
        return;
    }
    
    const coursesHtml = courses.map(course => `
        <div class="card mb-2">
            <div class="card-body p-3">
                <div class="d-flex justify-content-between align-items-start">
                    <div>
                        <h6 class="card-title mb-1">${course.course_name}</h6>
                        <p class="card-text small text-muted mb-1">${course.course_code}</p>
                        <p class="card-text small mb-0">
                            Attendance: <span class="fw-bold ${course.attendance_rate < 70 ? 'text-danger' : 'text-success'}">${course.attendance_rate}%</span>
                        </p>
                    </div>
                    <div class="text-end">
                        <span class="badge bg-${getGradeColor(course.current_grade)} mb-1">${course.current_grade || 'N/A'}</span>
                        <br>
                        <small class="text-muted">${course.credits} credits</small>
                    </div>
                </div>
            </div>
        </div>
    `).join('');
    
    container.innerHTML = coursesHtml;
}

function populateRecentAlerts(alerts) {
    const container = document.getElementById('recentAlerts');
    if (!container) return;
    
    if (alerts.length === 0) {
        container.innerHTML = '<p class="text-muted">No recent alerts</p>';
        return;
    }
    
    const alertsHtml = alerts.map(alert => `
        <div class="alert alert-${getSeverityColor(alert.severity)} alert-dismissible">
            <div class="d-flex justify-content-between align-items-start">
                <div>
                    <h6 class="alert-heading mb-1">${alert.title}</h6>
                    <p class="mb-1">${alert.message}</p>
                    <small class="text-muted">${formatDate(alert.created_at)}</small>
                </div>
                <span class="badge bg-${getSeverityColor(alert.severity)}">${alert.severity}</span>
            </div>
        </div>
    `).join('');
    
    container.innerHTML = alertsHtml;
}

async function loadAttendanceData(studentId) {
    try {
        const response = await apiClient.get(`faculty/students/${studentId}/attendance`);
        
        if (response.status === 'success') {
            createAttendanceChart(response.data.attendance_history);
            populateAttendanceTable(response.data.attendance_details);
        }
        
    } catch (error) {
        console.error('Error loading attendance data:', error);
        const chartElement = document.getElementById('attendanceChart');
        if (chartElement) {
            chartElement.innerHTML = '<p class="text-gray-500 text-center">Failed to load attendance data</p>';
        }
    }
}

async function loadGradeData(studentId) {
    try {
        const response = await apiClient.get(`faculty/students/${studentId}/grades`);
        
        if (response.status === 'success') {
            createGradeChart(response.data.grade_history);
            populateGradeTable(response.data.grade_details);
        }
        
    } catch (error) {
        console.error('Error loading grade data:', error);
        const chartElement = document.getElementById('gradeChart');
        if (chartElement) {
            chartElement.innerHTML = '<p class="text-gray-500 text-center">Failed to load grade data</p>';
        }
    }
}

async function loadInterventions(studentId) {
    try {
        const response = await apiClient.get(`faculty/students/${studentId}/interventions`);
        
        if (response.status === 'success') {
            populateInterventions(response.data.interventions);
        }
        
    } catch (error) {
        console.error('Error loading interventions:', error);
        const interventionsElement = document.getElementById('interventionsList');
        if (interventionsElement) {
            interventionsElement.innerHTML = '<p class="text-gray-500">Failed to load intervention history</p>';
        }
    }
}

function createAttendanceChart(attendanceHistory) {
    const ctx = document.getElementById('attendanceChart');
    if (!ctx) return;
    
    // Destroy existing chart
    if (attendanceChart) {
        attendanceChart.destroy();
    }
    
    const labels = attendanceHistory.map(item => item.date);
    const data = attendanceHistory.map(item => item.attendance_rate);
    
    attendanceChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Attendance Rate',
                data: data,
                borderColor: 'rgb(75, 192, 192)',
                backgroundColor: 'rgba(75, 192, 192, 0.2)',
                borderWidth: 2,
                fill: true,
                tension: 0.1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    ticks: {
                        callback: function(value) {
                            return value + '%';
                        }
                    }
                }
            },
            plugins: {
                title: {
                    display: true,
                    text: 'Attendance Trend'
                },
                legend: {
                    display: false
                }
            }
        }
    });
}

function createGradeChart(gradeHistory) {
    const ctx = document.getElementById('gradeChart');
    if (!ctx) return;
    
    // Destroy existing chart
    if (gradeChart) {
        gradeChart.destroy();
    }
    
    const labels = gradeHistory.map(item => item.assessment_name);
    const data = gradeHistory.map(item => item.score);
    
    gradeChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Score',
                data: data,
                backgroundColor: data.map(score => {
                    if (score >= 90) return 'rgba(40, 167, 69, 0.8)';
                    if (score >= 80) return 'rgba(23, 162, 184, 0.8)';
                    if (score >= 70) return 'rgba(255, 193, 7, 0.8)';
                    return 'rgba(220, 53, 69, 0.8)';
                }),
                borderColor: data.map(score => {
                    if (score >= 90) return 'rgba(40, 167, 69, 1)';
                    if (score >= 80) return 'rgba(23, 162, 184, 1)';
                    if (score >= 70) return 'rgba(255, 193, 7, 1)';
                    return 'rgba(220, 53, 69, 1)';
                }),
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    ticks: {
                        callback: function(value) {
                            return value + '%';
                        }
                    }
                }
            },
            plugins: {
                title: {
                    display: true,
                    text: 'Assessment Scores'
                },
                legend: {
                    display: false
                }
            }
        }
    });
}

function populateAttendanceTable(attendanceDetails) {
    const tbody = document.querySelector('#attendanceTable tbody');
    if (!tbody) return;
    
    if (attendanceDetails.length === 0) {
        tbody.innerHTML = '<tr><td colspan="4" class="text-center text-muted">No attendance records found</td></tr>';
        return;
    }
    
    tbody.innerHTML = attendanceDetails.map(record => `
        <tr>
            <td>${formatDate(record.date)}</td>
            <td>${record.course_name}</td>
            <td>
                <span class="badge bg-${getAttendanceColor(record.status)}">${record.status}</span>
            </td>
            <td>${record.notes || '-'}</td>
        </tr>
    `).join('');
}

function populateGradeTable(gradeDetails) {
    const tbody = document.querySelector('#gradeTable tbody');
    if (!tbody) return;
    
    if (gradeDetails.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted">No grade records found</td></tr>';
        return;
    }
    
    tbody.innerHTML = gradeDetails.map(grade => `
        <tr>
            <td>${grade.course_name}</td>
            <td>${grade.assessment_name}</td>
            <td>${grade.assessment_type}</td>
            <td>
                <span class="badge bg-${getGradeColor(grade.score)}">${grade.score}%</span>
            </td>
            <td>${formatDate(grade.submitted_date)}</td>
        </tr>
    `).join('');
}

function populateInterventions(interventions) {
    const container = document.getElementById('interventionsList');
    if (!container) return;
    
    if (interventions.length === 0) {
        container.innerHTML = '<p class="text-muted">No interventions recorded</p>';
        return;
    }
    
    const interventionsHtml = interventions.map(intervention => `
        <div class="card mb-3">
            <div class="card-body">
                <div class="d-flex justify-content-between align-items-start mb-2">
                    <h6 class="card-title mb-0">${intervention.title}</h6>
                    <span class="badge bg-${getInterventionColor(intervention.type)}">${intervention.type}</span>
                </div>
                <p class="card-text">${intervention.description}</p>
                <div class="row">
                    <div class="col-sm-6">
                        <small class="text-muted">
                            <strong>Date:</strong> ${formatDate(intervention.date)}
                        </small>
                    </div>
                    <div class="col-sm-6">
                        <small class="text-muted">
                            <strong>Follow-up:</strong> ${intervention.follow_up_date ? formatDate(intervention.follow_up_date) : 'None scheduled'}
                        </small>
                    </div>
                </div>
                ${intervention.outcome ? `
                    <div class="mt-2">
                        <small class="text-muted">
                            <strong>Outcome:</strong> ${intervention.outcome}
                        </small>
                    </div>
                ` : ''}
            </div>
        </div>
    `).join('');
    
    container.innerHTML = interventionsHtml;
}

function handleTabChange(tabId) {
    // Load specific content when tab changes
    switch(tabId) {
        case 'overview':
            // Overview is already loaded
            break;
        case 'attendance':
            // Attendance data is already loaded
            break;
        case 'grades':
            // Grade data is already loaded
            break;
        case 'interventions':
            // Intervention data is already loaded
            break;
    }
}

// Modal functions
function showSendAlertModal() {
    const modal = new bootstrap.Modal(document.getElementById('sendAlertModal'));
    modal.show();
}

function showScheduleMeetingModal() {
    const modal = new bootstrap.Modal(document.getElementById('scheduleMeetingModal'));
    modal.show();
}

function showAddNoteModal() {
    const modal = new bootstrap.Modal(document.getElementById('addNoteModal'));
    modal.show();
}

// Action handlers
async function sendAlert() {
    const form = document.getElementById('alertForm');
    const formData = new FormData(form);
    
    try {
        showButtonLoading('sendAlertSubmit');
        
        const response = await fetch(`/api/faculty/students/${studentData.student_id}/alert`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${getToken()}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                type: formData.get('alertType'),
                message: formData.get('alertMessage'),
                priority: formData.get('alertPriority')
            })
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {
            showSuccess('Alert sent successfully');
            bootstrap.Modal.getInstance(document.getElementById('sendAlertModal')).hide();
            form.reset();
            // Reload alerts
            loadStudentDetail(studentData.student_id);
        } else {
            throw new Error(data.message);
        }
        
    } catch (error) {
        console.error('Error sending alert:', error);
        showError('Failed to send alert');
    } finally {
        hideButtonLoading('sendAlertSubmit');
    }
}

async function scheduleMeeting() {
    const form = document.getElementById('meetingForm');
    const formData = new FormData(form);
    
    try {
        showButtonLoading('scheduleMeetingSubmit');
        
        const response = await fetch(`/api/faculty/students/${studentData.student_id}/meeting`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${getToken()}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                title: formData.get('meetingTitle'),
                date: formData.get('meetingDate'),
                time: formData.get('meetingTime'),
                notes: formData.get('meetingNotes')
            })
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {
            showSuccess('Meeting scheduled successfully');
            bootstrap.Modal.getInstance(document.getElementById('scheduleMeetingModal')).hide();
            form.reset();
        } else {
            throw new Error(data.message);
        }
        
    } catch (error) {
        console.error('Error scheduling meeting:', error);
        showError('Failed to schedule meeting');
    } finally {
        hideButtonLoading('scheduleMeetingSubmit');
    }
}

async function addNote() {
    const form = document.getElementById('noteForm');
    const formData = new FormData(form);
    
    try {
        showButtonLoading('addNoteSubmit');
        
        const response = await fetch(`/api/faculty/students/${studentData.student_id}/note`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${getToken()}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                title: formData.get('noteTitle'),
                content: formData.get('noteContent'),
                category: formData.get('noteCategory')
            })
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {
            showSuccess('Note added successfully');
            bootstrap.Modal.getInstance(document.getElementById('addNoteModal')).hide();
            form.reset();
            // Reload interventions
            loadInterventions(studentData.student_id);
        } else {
            throw new Error(data.message);
        }
        
    } catch (error) {
        console.error('Error adding note:', error);
        showError('Failed to add note');
    } finally {
        hideButtonLoading('addNoteSubmit');
    }
}

// Utility functions
function getRiskColor(riskLevel) {
    switch(riskLevel?.toLowerCase()) {
        case 'high': return 'danger';
        case 'medium': return 'warning';
        case 'low': return 'success';
        default: return 'secondary';
    }
}

function getGradeColor(grade) {
    if (grade >= 90) return 'success';
    if (grade >= 80) return 'info';
    if (grade >= 70) return 'warning';
    return 'danger';
}

function getSeverityColor(severity) {
    switch(severity?.toLowerCase()) {
        case 'critical': return 'danger';
        case 'warning': return 'warning';
        case 'info': return 'info';
        default: return 'secondary';
    }
}

function getAttendanceColor(status) {
    switch(status?.toLowerCase()) {
        case 'present': return 'success';
        case 'late': return 'warning';
        case 'absent': return 'danger';
        case 'excused': return 'info';
        default: return 'secondary';
    }
}

function getInterventionColor(type) {
    switch(type?.toLowerCase()) {
        case 'meeting': return 'primary';
        case 'alert': return 'warning';
        case 'counseling': return 'info';
        case 'academic_support': return 'success';
        default: return 'secondary';
    }
}

function formatDate(dateString) {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

function getToken() {
    return localStorage.getItem('accessToken');
}

function showLoading() {
    const loadingDiv = document.getElementById('loadingIndicator');
    if (loadingDiv) {
        loadingDiv.style.display = 'block';
    }
}

function hideLoading() {
    const loadingDiv = document.getElementById('loadingIndicator');
    if (loadingDiv) {
        loadingDiv.style.display = 'none';
    }
}

function showButtonLoading(buttonId) {
    const button = document.getElementById(buttonId);
    if (button) {
        button.disabled = true;
        button.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Processing...';
    }
}

function hideButtonLoading(buttonId) {
    const button = document.getElementById(buttonId);
    if (button) {
        button.disabled = false;
        // Reset button text based on its original purpose
        if (buttonId === 'sendAlertSubmit') {
            button.innerHTML = 'Send Alert';
        } else if (buttonId === 'scheduleMeetingSubmit') {
            button.innerHTML = 'Schedule Meeting';
        } else if (buttonId === 'addNoteSubmit') {
            button.innerHTML = 'Add Note';
        }
    }
}

function showSuccess(message) {
    // Create and show success toast/alert
    const alert = document.createElement('div');
    alert.className = 'alert alert-success alert-dismissible fade show position-fixed top-0 end-0 m-3';
    alert.style.zIndex = '9999';
    alert.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    document.body.appendChild(alert);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        if (alert.parentNode) {
            alert.parentNode.removeChild(alert);
        }
    }, 5000);
}

function showError(message) {
    // Create and show error toast/alert
    const alert = document.createElement('div');
    alert.className = 'alert alert-danger alert-dismissible fade show position-fixed top-0 end-0 m-3';
    alert.style.zIndex = '9999';
    alert.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    document.body.appendChild(alert);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        if (alert.parentNode) {
            alert.parentNode.removeChild(alert);
        }
    }, 5000);
}

function logout() {
    localStorage.removeItem('accessToken');
    window.location.href = '/auth/login.html';
}