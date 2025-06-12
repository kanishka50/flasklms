document.addEventListener('DOMContentLoaded', function() {
    // Elements
    const usernameElement = document.getElementById('username');
    const logoutBtn = document.getElementById('logoutBtn');
    
    // Dashboard summary elements
    const courseCount = document.getElementById('courseCount');
    const studentCount = document.getElementById('studentCount');
    const atRiskCount = document.getElementById('atRiskCount');
    const totalAssessments = document.getElementById('totalAssessments');
    const totalAssessmentsDetail = document.getElementById('totalAssessmentsDetail');
    const gradedSubmissions = document.getElementById('gradedSubmissions');
    
    // Content elements
    const coursesList = document.getElementById('coursesList');
    const recentAssessmentsList = document.getElementById('recentAssessmentsList');
    const atRiskStudentsList = document.getElementById('atRiskStudentsList');
    
    // Initialize
    init();
    
    function init() {
        // Check authentication
        if (!authApi.isLoggedIn()) {
            window.location.href = '../login.html';
            return;
        }
        
        // Check user role
        if (!authApi.hasRole('faculty')) {
            window.location.href = '../login.html';
            return;
        }
        
        // Display username
        const user = authApi.getCurrentUser();
        if (user) {
            usernameElement.textContent = user.username;
        }
        
        // Load all dashboard data
        loadDashboardData();
        
        // Set up event listeners
        setupEventListeners();
    }
    
    function setupEventListeners() {
        // Logout
        logoutBtn.addEventListener('click', function() {
            authApi.logout();
        });
    }
    
    async function loadDashboardData() {
        try {
            // Load dashboard summary
            await loadDashboardSummary();
            
            // Load courses
            await loadCourses();
            
            // Load recent assessments
            await loadRecentAssessments();
            
            // Load at-risk students
            await loadAtRiskStudents();
            
        } catch (error) {
            console.error('Error loading dashboard data:', error);
        }
    }
    
    async function loadDashboardSummary() {
        try {
            const response = await apiClient.get('faculty/dashboard');
            console.log('Dashboard summary response:', response);
            
            if (response.status === 'success' && response.data) {
                const summary = response.data.summary;
                
                // Update summary cards
                if (courseCount) courseCount.textContent = summary.course_count || 0;
                if (studentCount) studentCount.textContent = summary.student_count || 0;
                if (atRiskCount) atRiskCount.textContent = summary.at_risk_count || 0;
                
                // Assessment counts will be loaded separately
            }
        } catch (error) {
            console.error('Error loading dashboard summary:', error);
            // Set default values
            if (courseCount) courseCount.textContent = '0';
            if (studentCount) studentCount.textContent = '0';
            if (atRiskCount) atRiskCount.textContent = '0';
        }
    }
    
    async function loadCourses() {
        try {
            const response = await apiClient.get('faculty/courses');
            console.log('Courses response:', response);
            
            if (response.status === 'success' && response.data) {
                displayCourses(response.data.courses);
            } else {
                coursesList.innerHTML = '<p class="text-gray-500">No courses found</p>';
            }
        } catch (error) {
            console.error('Error loading courses:', error);
            coursesList.innerHTML = '<p class="text-red-500">Error loading courses</p>';
        }
    }
    
    async function loadRecentAssessments() {
        try {
            const response = await apiClient.get('faculty/assessments');
            console.log('Assessments response:', response);
            
            if (response.status === 'success' && response.data) {
                displayRecentAssessments(response.data.assessments);
                updateAssessmentStats(response.data.assessments);
            } else {
                recentAssessmentsList.innerHTML = '<p class="text-gray-500">No assessments found</p>';
            }
        } catch (error) {
            console.error('Error loading assessments:', error);
            recentAssessmentsList.innerHTML = '<p class="text-gray-500">No recent assessments</p>';
            // Set default assessment counts
            if (totalAssessments) totalAssessments.textContent = '0';
            if (totalAssessmentsDetail) totalAssessmentsDetail.textContent = '0';
            if (gradedSubmissions) gradedSubmissions.textContent = '0';
        }
    }
    
    async function loadAtRiskStudents() {
        try {
            const response = await apiClient.get('faculty/at-risk-students');
            console.log('At-risk students response:', response);
            
            if (response.status === 'success' && response.data) {
                displayAtRiskStudents(response.data.students);
            } else {
                atRiskStudentsList.innerHTML = '<p class="text-gray-500">No at-risk students found</p>';
            }
        } catch (error) {
            console.error('Error loading at-risk students:', error);
            atRiskStudentsList.innerHTML = '<p class="text-gray-500">Unable to load at-risk students</p>';
        }
    }
    
    function displayCourses(courses) {
        if (!courses || courses.length === 0) {
            coursesList.innerHTML = '<p class="text-gray-500">No courses assigned</p>';
            return;
        }
        
        // Show only first 3 courses
        const displayCourses = courses.slice(0, 3);
        
        let html = '';
        displayCourses.forEach(course => {
            const statusColor = course.enrollment_status === 'completed' ? 'text-green-600' : 'text-blue-600';
            
            html += `
                <div class="border-b pb-3 mb-3 last:border-b-0">
                    <div class="flex justify-between items-start">
                        <div>
                            <h4 class="font-semibold text-gray-900">${course.course_name}</h4>
                            <p class="text-sm text-gray-600">${course.course_code} • Section ${course.section}</p>
                            <p class="text-xs text-gray-500">${course.enrolled_count || 0} students enrolled</p>
                        </div>
                        <div class="text-right">
                            <a href="students.html?course=${course.offering_id}" class="text-blue-600 hover:text-blue-800 text-sm">
                                View Students →
                            </a>
                        </div>
                    </div>
                </div>
            `;
        });
        
        if (courses.length > 3) {
            html += `
                <div class="text-center pt-2">
                    <a href="courses.html" class="text-blue-600 hover:text-blue-800 text-sm font-medium">
                        View all ${courses.length} courses →
                    </a>
                </div>
            `;
        }
        
        coursesList.innerHTML = html;
    }
    
    function displayRecentAssessments(assessments) {
        if (!assessments || assessments.length === 0) {
            recentAssessmentsList.innerHTML = '<p class="text-gray-500 text-sm">No recent assessments</p>';
            return;
        }
        
        // Show only first 3 recent assessments
        const recentAssessments = assessments.slice(0, 3);
        
        recentAssessmentsList.innerHTML = recentAssessments.map(assessment => {
            const dueDate = assessment.due_date ? new Date(assessment.due_date) : null;
            const isOverdue = dueDate && new Date() > dueDate;
            
            return `
                <div class="flex justify-between items-center p-3 border border-gray-200 rounded-lg hover:bg-gray-50">
                    <div>
                        <div class="font-medium text-sm text-gray-900">${assessment.title}</div>
                        <div class="text-xs text-gray-500">${assessment.course_code} • ${assessment.type_name}</div>
                        ${dueDate ? `
                            <div class="text-xs ${isOverdue ? 'text-red-600' : 'text-gray-400'}">
                                Due: ${dueDate.toLocaleDateString()}
                            </div>
                        ` : ''}
                    </div>
                    <div class="text-right">
                        <div class="text-sm font-medium text-gray-900">${assessment.submitted_count || 0}/${assessment.total_students || 0}</div>
                        <div class="text-xs text-gray-500">Submitted</div>
                        <a href="assessment-grade.html?assessment_id=${assessment.assessment_id}" class="text-blue-600 hover:text-blue-800 text-xs">
                            Grade →
                        </a>
                    </div>
                </div>
            `;
        }).join('');
    }
    
    function updateAssessmentStats(assessments) {
        if (!assessments) {
            if (totalAssessments) totalAssessments.textContent = '0';
            if (totalAssessmentsDetail) totalAssessmentsDetail.textContent = '0';
            if (gradedSubmissions) gradedSubmissions.textContent = '0';
            return;
        }
        
        const totalCount = assessments.length;
        const totalGraded = assessments.reduce((sum, assessment) => {
            return sum + (assessment.graded_count || 0);
        }, 0);
        
        if (totalAssessments) totalAssessments.textContent = totalCount;
        if (totalAssessmentsDetail) totalAssessmentsDetail.textContent = totalCount;
        if (gradedSubmissions) gradedSubmissions.textContent = totalGraded;
    }
    
    function displayAtRiskStudents(students) {
        if (!students || students.length === 0) {
            atRiskStudentsList.innerHTML = '<p class="text-gray-500">No at-risk students identified</p>';
            return;
        }
        
        // Show only first 5 at-risk students
        const displayStudents = students.slice(0, 5);
        
        let html = '';
        displayStudents.forEach(student => {
            const riskColor = student.risk_level === 'high' ? 'text-red-600' : 
                             student.risk_level === 'medium' ? 'text-yellow-600' : 'text-blue-600';
            
            html += `
                <div class="border-b pb-3 mb-3 last:border-b-0">
                    <div class="flex justify-between items-start">
                        <div>
                            <h4 class="font-semibold text-gray-900">${student.student_name}</h4>
                            <p class="text-sm text-gray-600">${student.course_code} • ID: ${student.student_id}</p>
                            <p class="text-sm ${riskColor}">Risk Level: ${student.risk_level}</p>
                        </div>
                        <div class="text-right">
                            <div class="text-sm font-medium ${riskColor}">${student.predicted_grade}</div>
                            <div class="text-xs text-gray-500">Predicted</div>
                        </div>
                    </div>
                </div>
            `;
        });
        
        if (students.length > 5) {
            html += `
                <div class="text-center pt-2">
                    <a href="students.html" class="text-blue-600 hover:text-blue-800 text-sm font-medium">
                        View all ${students.length} at-risk students →
                    </a>
                </div>
            `;
        }
        
        atRiskStudentsList.innerHTML = html;
    }
});