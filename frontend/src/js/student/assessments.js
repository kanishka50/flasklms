document.addEventListener('DOMContentLoaded', function() {
    // Elements
    const usernameElement = document.getElementById('username');
    const logoutBtn = document.getElementById('logoutBtn');
    const courseFilter = document.getElementById('courseFilter');
    const statusFilter = document.getElementById('statusFilter');
    const refreshBtn = document.getElementById('refreshBtn');
    const loadingIndicator = document.getElementById('loadingIndicator');
    const assessmentsContainer = document.getElementById('assessmentsContainer');
    const noAssessments = document.getElementById('noAssessments');
    
    // Stats elements
    const totalAssessments = document.getElementById('totalAssessments');
    const gradedAssessments = document.getElementById('gradedAssessments');
    const pendingAssessments = document.getElementById('pendingAssessments');
    const averageGrade = document.getElementById('averageGrade');
    
    // Modal elements
    const assessmentModal = document.getElementById('assessmentModal');
    const modalTitle = document.getElementById('modalTitle');
    const modalContent = document.getElementById('modalContent');
    const closeModal = document.getElementById('closeModal');
    
    // State
    let allAssessments = [];
    let coursesList = [];
    
    // Initialize
    init();
    
    function init() {
        // Check authentication
        if (!authApi.isLoggedIn()) {
            window.location.href = '../login.html';
            return;
        }
        
        // Check user role
        if (!authApi.hasRole('student')) {
            window.location.href = '../login.html';
            return;
        }
        
        // Display username
        const user = authApi.getCurrentUser();
        if (user) {
            usernameElement.textContent = user.username;
        }
        
        // Load assessments
        loadAllAssessments();
        
        // Set up event listeners
        setupEventListeners();
    }
    
    function setupEventListeners() {
        // Logout
        logoutBtn.addEventListener('click', function() {
            authApi.logout();
        });
        
        // Refresh button
        refreshBtn.addEventListener('click', function() {
            loadAllAssessments();
        });
        
        // Filter changes
        courseFilter.addEventListener('change', filterAssessments);
        statusFilter.addEventListener('change', filterAssessments);
        
        // Modal close
        closeModal.addEventListener('click', function() {
            assessmentModal.classList.add('hidden');
        });
        
        // Close modal on outside click
        assessmentModal.addEventListener('click', function(e) {
            if (e.target === assessmentModal) {
                assessmentModal.classList.add('hidden');
            }
        });
    }
    
    async function loadAllAssessments() {
        try {
            showLoading(true);
            
            console.log('Loading all student assessments...');
            const response = await apiClient.get('student/assessments/all');
            console.log('Assessments response:', response);
            
            if (response.status === 'success' && response.data) {
                coursesList = response.data.courses || [];
                
                // Flatten assessments for easier processing
                allAssessments = [];
                coursesList.forEach(course => {
                    course.assessments.forEach(assessment => {
                        allAssessments.push({
                            ...assessment,
                            course_info: {
                                course_code: course.course_code,
                                course_name: course.course_name
                            }
                        });
                    });
                });
                
                populateCourseFilter();
                updateStats();
                displayAssessments(coursesList);
            } else {
                showNoAssessments();
            }
        } catch (error) {
            console.error('Error loading assessments:', error);
            if (error.response && error.response.status === 401) {
                authApi.logout();
            } else {
                showError('Failed to load assessments. Please refresh the page.');
            }
        } finally {
            showLoading(false);
        }
    }
    
    function populateCourseFilter() {
        courseFilter.innerHTML = '<option value="">All Courses</option>';
        
        coursesList.forEach(course => {
            const option = document.createElement('option');
            option.value = course.course_code;
            option.textContent = `${course.course_code} - ${course.course_name}`;
            courseFilter.appendChild(option);
        });
    }
    
    function updateStats() {
        const total = allAssessments.length;
        const graded = allAssessments.filter(a => a.status === 'graded').length;
        const pending = total - graded;
        
        totalAssessments.textContent = total;
        gradedAssessments.textContent = graded;
        pendingAssessments.textContent = pending;
        
        // Calculate average percentage
        const gradedWithScores = allAssessments.filter(a => a.percentage !== null);
        if (gradedWithScores.length > 0) {
            const avg = gradedWithScores.reduce((sum, a) => sum + a.percentage, 0) / gradedWithScores.length;
            averageGrade.textContent = avg.toFixed(1) + '%';
        } else {
            averageGrade.textContent = '-';
        }
    }
    
    function filterAssessments() {
        const courseFilter_value = courseFilter.value;
        const statusFilter_value = statusFilter.value;
        
        let filteredCourses = coursesList.map(course => ({
            ...course,
            assessments: course.assessments.filter(assessment => {
                // Course filter
                if (courseFilter_value && course.course_code !== courseFilter_value) {
                    return false;
                }
                
                // Status filter
                if (statusFilter_value) {
                    if (statusFilter_value === 'overdue') {
                        const dueDate = new Date(assessment.due_date);
                        const now = new Date();
                        return assessment.status !== 'graded' && dueDate < now;
                    } else {
                        return assessment.status === statusFilter_value;
                    }
                }
                
                return true;
            })
        })).filter(course => course.assessments.length > 0);
        
        displayAssessments(filteredCourses);
    }
    
    function displayAssessments(courses) {
        if (!courses.length || courses.every(c => c.assessments.length === 0)) {
            showNoAssessments();
            return;
        }
        
        assessmentsContainer.innerHTML = '';
        
        courses.forEach(course => {
            if (course.assessments.length === 0) return;
            
            const courseSection = createCourseSection(course);
            assessmentsContainer.appendChild(courseSection);
        });
        
        assessmentsContainer.classList.remove('hidden');
        noAssessments.classList.add('hidden');
    }
    
    function createCourseSection(course) {
        const section = document.createElement('div');
        section.className = 'bg-white rounded-lg shadow-md overflow-hidden';
        
        section.innerHTML = `
            <div class="bg-gray-50 px-6 py-4 border-b">
                <h3 class="text-lg font-semibold text-gray-900">${course.course_code} - ${course.course_name}</h3>
                <p class="text-sm text-gray-600">${course.assessments.length} assessment(s)</p>
            </div>
            <div class="divide-y divide-gray-200">
                ${course.assessments.map(assessment => createAssessmentCard(assessment)).join('')}
            </div>
        `;
        
        return section;
    }
    
    function createAssessmentCard(assessment) {
        const dueDate = assessment.due_date ? new Date(assessment.due_date) : null;
        const isOverdue = dueDate && new Date() > dueDate && assessment.status !== 'graded';
        
        const statusBadge = getStatusBadge(assessment.status, isOverdue);
        const gradeBadge = getGradeBadge(assessment.percentage);
        
        return `
            <div class="p-6 hover:bg-gray-50 cursor-pointer assessment-card" data-assessment='${JSON.stringify(assessment)}'>
                <div class="flex justify-between items-start">
                    <div class="flex-1">
                        <div class="flex items-center space-x-3 mb-2">
                            <h4 class="text-lg font-medium text-gray-900">${assessment.title}</h4>
                            ${statusBadge}
                            ${gradeBadge}
                        </div>
                        <div class="flex items-center space-x-4 text-sm text-gray-500 mb-2">
                            <span class="flex items-center">
                                <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z"></path>
                                </svg>
                                ${assessment.type_name}
                            </span>
                            ${dueDate ? `
                                <span class="flex items-center ${isOverdue ? 'text-red-600' : ''}">
                                    <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
                                    </svg>
                                    Due: ${dueDate.toLocaleDateString()} ${dueDate.toLocaleTimeString()}
                                </span>
                            ` : ''}
                        </div>
                        ${assessment.score !== null ? `
                            <div class="text-sm text-gray-600">
                                Score: <span class="font-medium">${assessment.score}/${assessment.max_score}</span>
                                (${assessment.percentage?.toFixed(1)}%)
                            </div>
                        ` : `
                            <div class="text-sm text-gray-600">
                                Max Score: <span class="font-medium">${assessment.max_score}</span>
                            </div>
                        `}
                    </div>
                    <div class="text-right">
                        <button class="text-blue-600 hover:text-blue-800 text-sm font-medium">
                            View Details →
                        </button>
                    </div>
                </div>
            </div>
        `;
    }
    
    function getStatusBadge(status, isOverdue) {
        if (isOverdue) {
            return '<span class="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-red-100 text-red-800">Overdue</span>';
        }
        
        switch (status) {
            case 'graded':
                return '<span class="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-800">Graded</span>';
            case 'pending':
                return '<span class="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-yellow-100 text-yellow-800">Pending</span>';
            default:
                return '<span class="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-gray-100 text-gray-800">Not Submitted</span>';
        }
    }
    
    function getGradeBadge(percentage) {
        if (percentage === null || percentage === undefined) return '';
        
        let grade, colorClass;
        if (percentage >= 90) {
            grade = 'A';
            colorClass = 'bg-green-100 text-green-800';
        } else if (percentage >= 80) {
            grade = 'B';
            colorClass = 'bg-blue-100 text-blue-800';
        } else if (percentage >= 70) {
            grade = 'C';
            colorClass = 'bg-yellow-100 text-yellow-800';
        } else if (percentage >= 60) {
            grade = 'D';
            colorClass = 'bg-orange-100 text-orange-800';
        } else {
            grade = 'F';
            colorClass = 'bg-red-100 text-red-800';
        }
        
        return `<span class="inline-flex px-2 py-1 text-xs font-semibold rounded-full ${colorClass}">${grade}</span>`;
    }
    
    function showAssessmentDetails(assessment) {
        modalTitle.textContent = assessment.title;
        
        const dueDate = assessment.due_date ? new Date(assessment.due_date) : null;
        const submissionDate = assessment.submission_date ? new Date(assessment.submission_date) : null;
        
        modalContent.innerHTML = `
            <div class="space-y-4">
                <div class="grid grid-cols-2 gap-4">
                    <div>
                        <label class="block text-sm font-medium text-gray-700">Course</label>
                        <p class="text-sm text-gray-900">${assessment.course_code} - ${assessment.course_name}</p>
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700">Type</label>
                        <p class="text-sm text-gray-900">${assessment.type_name}</p>
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700">Maximum Score</label>
                        <p class="text-sm text-gray-900">${assessment.max_score} points</p>
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700">Weight</label>
                        <p class="text-sm text-gray-900">${assessment.weight || 'Not specified'}${assessment.weight ? '%' : ''}</p>
                    </div>
                    ${dueDate ? `
                        <div>
                            <label class="block text-sm font-medium text-gray-700">Due Date</label>
                            <p class="text-sm text-gray-900">${dueDate.toLocaleDateString()} ${dueDate.toLocaleTimeString()}</p>
                        </div>
                    ` : ''}
                    ${assessment.score !== null ? `
                        <div>
                            <label class="block text-sm font-medium text-gray-700">Your Score</label>
                            <p class="text-sm text-gray-900 font-semibold">${assessment.score}/${assessment.max_score} (${assessment.percentage?.toFixed(1)}%)</p>
                        </div>
                    ` : ''}
                </div>
                
                ${assessment.description ? `
                    <div>
                        <label class="block text-sm font-medium text-gray-700">Description</label>
                        <p class="text-sm text-gray-900 bg-gray-50 p-3 rounded-md">${assessment.description}</p>
                    </div>
                ` : ''}
                
                ${assessment.feedback ? `
                    <div>
                        <label class="block text-sm font-medium text-gray-700">Feedback</label>
                        <p class="text-sm text-gray-900 bg-blue-50 p-3 rounded-md">${assessment.feedback}</p>
                    </div>
                ` : ''}
                
                ${submissionDate ? `
                    <div>
                        <label class="block text-sm font-medium text-gray-700">Submission Date</label>
                        <p class="text-sm text-gray-900">${submissionDate.toLocaleDateString()} ${submissionDate.toLocaleTimeString()}</p>
                        ${assessment.is_late ? '<span class="text-xs text-red-600 font-medium">Late Submission</span>' : ''}
                    </div>
                ` : ''}
            </div>
        `;
        
        assessmentModal.classList.remove('hidden');
    }
    
    function showLoading(show) {
        if (show) {
            loadingIndicator.classList.remove('hidden');
            assessmentsContainer.classList.add('hidden');
            noAssessments.classList.add('hidden');
        } else {
            loadingIndicator.classList.add('hidden');
        }
    }
    
    function showNoAssessments() {
        assessmentsContainer.classList.add('hidden');
        noAssessments.classList.remove('hidden');
    }
    
    function showError(message) {
        console.error(message);
        // You can implement a toast notification here
        alert(message);
    }
    
    // Event delegation for assessment cards
    document.addEventListener('click', function(e) {
        const assessmentCard = e.target.closest('.assessment-card');
        if (assessmentCard) {
            const assessment = JSON.parse(assessmentCard.dataset.assessment);
            showAssessmentDetails(assessment);
        }
    });
});