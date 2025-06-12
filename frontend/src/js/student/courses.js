// Fixed Student Courses Management - Replace your existing courses.js
document.addEventListener('DOMContentLoaded', function() {
    // Elements
    const usernameElement = document.getElementById('username');
    const logoutBtn = document.getElementById('logoutBtn');
    const refreshBtn = document.getElementById('refreshBtn');
    const enrollBtn = document.getElementById('enrollBtn');
    
    // Filter elements
    const termFilter = document.getElementById('termFilter');
    const searchCourses = document.getElementById('searchCourses');
    const statusFilter = document.getElementById('statusFilter');
    
    // Stats elements
    const totalCoursesCount = document.getElementById('totalCoursesCount');
    const currentGPA = document.getElementById('currentGPA');
    const overallAttendance = document.getElementById('overallAttendance');
    const atRiskCoursesCount = document.getElementById('atRiskCoursesCount');
    
    // Content elements
    const coursesContainer = document.getElementById('coursesContainer');
    const emptyState = document.getElementById('emptyState');
    const attendanceTrend = document.getElementById('attendanceTrend');
    
    // Modal elements
    const courseModal = document.getElementById('courseModal');
    const modalCourseTitle = document.getElementById('modalCourseTitle');
    const courseModalContent = document.getElementById('courseModalContent');
    const closeCourseModal = document.getElementById('closeCourseModal');
    
    const quickActionsModal = document.getElementById('quickActionsModal');
    const quickActionsContent = document.getElementById('quickActionsContent');
    const closeQuickActionsModal = document.getElementById('closeQuickActionsModal');
    
    // State
    let allCourses = [];
    let filteredCourses = [];
    let dashboardSummary = {};
    let gradeChart = null;
    let isLoading = false;
    let isInitialized = false; // Prevent multiple initializations
    let eventListenersAttached = false; // Prevent duplicate event listeners
    
    // Initialize
    init();
    
    function init() {
        if (isInitialized) return; // Prevent multiple initializations
        
        // Check authentication
        if (!authApi.isLoggedIn()) {
            window.location.href = '../login.html';
            return;
        }
        
        if (!authApi.hasRole('student')) {
            window.location.href = '../login.html';
            return;
        }
        
        // Display username
        const user = authApi.getCurrentUser();
        if (user) {
            usernameElement.textContent = user.username;
        }
        
        // Setup event listeners only once
        if (!eventListenersAttached) {
            setupEventListeners();
            eventListenersAttached = true;
        }
        
        isInitialized = true;
        
        // Load data with a single call
        loadAllData();
    }
    
    function setupEventListeners() {
        // Logout
        logoutBtn?.addEventListener('click', handleLogout);
        
        // Refresh
        refreshBtn?.addEventListener('click', handleRefresh);
        
        // Enroll button
        enrollBtn?.addEventListener('click', handleEnrollClick);
        
        // Search with debounce
        let searchTimeout;
        searchCourses?.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                filterCourses();
            }, 300);
        });
        
        // Term filter
        termFilter?.addEventListener('change', handleTermChange);
        
        // Status filter
        statusFilter?.addEventListener('change', filterCourses);
        
        // Modal event listeners
        closeCourseModal?.addEventListener('click', () => {
            courseModal?.classList.add('hidden');
        });
        
        closeQuickActionsModal?.addEventListener('click', () => {
            quickActionsModal?.classList.add('hidden');
        });
        
        // Close modals on backdrop click
        courseModal?.addEventListener('click', function(e) {
            if (e.target === courseModal) {
                courseModal.classList.add('hidden');
            }
        });
        
        quickActionsModal?.addEventListener('click', function(e) {
            if (e.target === quickActionsModal) {
                quickActionsModal.classList.add('hidden');
            }
        });
    }
    
    // Event handlers to prevent multiple calls
    function handleLogout() {
        authApi.logout();
        window.location.href = '../login.html';
    }
    
    function handleRefresh() {
        if (!isLoading) {
            loadAllData();
        }
    }
    
    function handleEnrollClick() {
        showNotification('Course enrollment feature coming soon!', 'info');
    }
    
    function handleTermChange() {
        if (!isLoading) {
            loadCourses();
        }
    }
    
    async function loadAllData() {
        if (isLoading) return; // Prevent multiple simultaneous loads
        
        try {
            isLoading = true;
            showLoading();
            
            // Load dashboard summary and courses in parallel
            const [dashboardResult, coursesResult] = await Promise.allSettled([
                loadDashboardSummary(),
                loadCourses()
            ]);
            
            // Handle results
            if (dashboardResult.status === 'fulfilled') {
                updateDashboardStats();
            } else {
                console.warn('Dashboard summary failed:', dashboardResult.reason);
            }
            
            if (coursesResult.status === 'fulfilled') {
                displayCourses();
                updateStats();
                // Update charts only once, safely
                requestAnimationFrame(() => {
                    updateProgressCharts();
                });
            } else {
                console.error('Courses loading failed:', coursesResult.reason);
                showError('Failed to load courses');
            }
            
        } catch (error) {
            console.error('Error loading data:', error);
            showError('Failed to load course data');
        } finally {
            isLoading = false;
        }
    }
    
    async function loadDashboardSummary() {
        try {
            console.log('Loading dashboard summary...');
            const response = await apiClient.get('student/dashboard');
            
            if (response.status === 'success' && response.data) {
                dashboardSummary = response.data.summary || {};
                return dashboardSummary;
            } else {
                // Fallback data if API returns error
                dashboardSummary = {
                    gpa: 0,
                    attendance_rate: 0,
                    upcoming_assessments: 0
                };
                return dashboardSummary;
            }
        } catch (error) {
            console.warn('Dashboard summary not available:', error);
            dashboardSummary = {
                gpa: 0,
                attendance_rate: 0,
                upcoming_assessments: 0
            };
            return dashboardSummary;
        }
    }
    
    async function loadCourses() {
        try {
            console.log('Loading student courses...');
            
            // Get term from filter
            const termId = termFilter?.value || null;
            let url = 'student/courses';
            if (termId) {
                url += `?term_id=${termId}`;
            }
            
            const response = await apiClient.get(url);
            console.log('Courses response:', response);
            
            if (response.status === 'success' && response.data && response.data.courses) {
                allCourses = response.data.courses;
                filteredCourses = [...allCourses];
                return allCourses;
            } else {
                // Handle case where API returns success but no courses
                allCourses = [];
                filteredCourses = [];
                return allCourses;
            }
        } catch (error) {
            console.error('Error loading courses:', error);
            // Set mock data for development/testing
            allCourses = getMockCourses();
            filteredCourses = [...allCourses];
            return allCourses;
        }
    }
    
    // Mock data for development/testing
    function getMockCourses() {
        return [
            {
                course_id: 1,
                course_code: 'CS101',
                course_name: 'Introduction to Computer Science',
                section: 'A',
                credits: 3,
                instructor_name: 'Dr. Smith',
                instructor_email: 'smith@university.edu',
                meeting_pattern: 'MWF 9:00-10:00 AM',
                location: 'Room 101',
                enrollment_status: 'enrolled',
                current_grade: 'B+',
                predicted_grade: 'A-',
                attendance_rate: 85,
                next_assessment: 'Midterm - Oct 15'
            },
            {
                course_id: 2,
                course_code: 'MATH201',
                course_name: 'Calculus II',
                section: 'B',
                credits: 4,
                instructor_name: 'Dr. Johnson',
                instructor_email: 'johnson@university.edu',
                meeting_pattern: 'TTh 2:00-3:30 PM',
                location: 'Room 205',
                enrollment_status: 'enrolled',
                current_grade: 'C+',
                predicted_grade: 'B',
                attendance_rate: 75,
                next_assessment: 'Quiz - Oct 12'
            }
        ];
    }
    
    function displayCourses() {
        if (!filteredCourses || filteredCourses.length === 0) {
            showEmptyState();
            return;
        }
        
        hideEmptyState();
        const html = filteredCourses.map(course => createCourseCard(course)).join('');
        coursesContainer.innerHTML = html;
        
        // Attach event listeners to new course cards
        attachCourseCardListeners();
    }
    
    function createCourseCard(course) {
        const attendanceRate = course.attendance_rate || 0;
        const predictedGrade = course.predicted_grade || 'N/A';
        const currentGrade = course.current_grade || 'N/A';
        
        // Determine colors and status
        const attendanceColor = attendanceRate >= 80 ? 'text-green-600' :
                               attendanceRate >= 60 ? 'text-yellow-600' : 'text-red-600';
        
        const gradeColor = ['A', 'A-', 'B+', 'B'].includes(predictedGrade) ? 'text-green-600' :
                          ['B-', 'C+', 'C'].includes(predictedGrade) ? 'text-yellow-600' : 
                          ['C-', 'D+', 'D', 'D-', 'F'].includes(predictedGrade) ? 'text-red-600' : 'text-gray-600';
        
        const statusColor = course.enrollment_status === 'completed' ? 
            'bg-gray-100 text-gray-800' : 'bg-green-100 text-green-800';
        
        const isAtRisk = ['C-', 'D+', 'D', 'D-', 'F'].includes(predictedGrade) || attendanceRate < 60;
        
        return `
            <div class="bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow duration-300 course-card cursor-pointer" 
                 data-course-id="${course.course_id || ''}" data-enrollment-id="${course.enrollment_id || ''}">
                <div class="p-6">
                    <!-- Course Header -->
                    <div class="flex justify-between items-start mb-4">
                        <div class="flex-1">
                            <h3 class="text-lg font-semibold text-gray-900 mb-1">
                                ${course.course_name || 'Course Name'}
                            </h3>
                            <p class="text-sm text-gray-600 mb-1">
                                ${course.course_code || 'N/A'} • Section ${course.section || 'N/A'} • ${course.credits || 0} Credits
                            </p>
                            <p class="text-xs text-gray-500">
                                Instructor: ${course.instructor_name || 'TBA'}
                            </p>
                        </div>
                        <div class="flex flex-col items-end space-y-1">
                            <span class="px-2 py-1 text-xs font-medium rounded-full ${statusColor}">
                                ${course.enrollment_status || 'Enrolled'}
                            </span>
                            ${isAtRisk ? '<span class="px-2 py-1 text-xs font-medium rounded-full bg-red-100 text-red-800">At Risk</span>' : ''}
                        </div>
                    </div>
                    
                    <!-- Progress Stats -->
                    <div class="grid grid-cols-3 gap-3 mb-4">
                        <div class="text-center p-3 bg-gray-50 rounded-lg">
                            <div class="text-lg font-bold ${attendanceColor}">${Math.round(attendanceRate)}%</div>
                            <div class="text-xs text-gray-600">Attendance</div>
                        </div>
                        <div class="text-center p-3 bg-gray-50 rounded-lg">
                            <div class="text-lg font-bold text-blue-600">${currentGrade}</div>
                            <div class="text-xs text-gray-600">Current</div>
                        </div>
                        <div class="text-center p-3 bg-gray-50 rounded-lg">
                            <div class="text-lg font-bold ${gradeColor}">${predictedGrade}</div>
                            <div class="text-xs text-gray-600">Predicted</div>
                        </div>
                    </div>
                    
                    <!-- Course Details -->
                    <div class="space-y-1 mb-4 text-sm text-gray-600">
                        <div class="flex items-center">
                            <i class="fas fa-clock w-4 mr-2"></i>
                            <span>${course.meeting_pattern || 'Schedule TBA'}</span>
                        </div>
                        <div class="flex items-center">
                            <i class="fas fa-map-marker-alt w-4 mr-2"></i>
                            <span>${course.location || 'Location TBA'}</span>
                        </div>
                        ${course.next_assessment ? `
                        <div class="flex items-center text-orange-600">
                            <i class="fas fa-clipboard-list w-4 mr-2"></i>
                            <span>Next: ${course.next_assessment}</span>
                        </div>
                        ` : ''}
                    </div>
                    
                    <!-- Action Buttons -->
                    <div class="flex space-x-2">
                        <button class="flex-1 bg-blue-600 text-white py-2 px-3 rounded text-sm hover:bg-blue-700 view-details-btn"
                                data-course-id="${course.course_id || ''}" onclick="event.stopPropagation()">
                            <i class="fas fa-eye mr-1"></i> Details
                        </button>
                        <button class="flex-1 bg-green-600 text-white py-2 px-3 rounded text-sm hover:bg-green-700 quick-actions-btn"
                                data-course-id="${course.course_id || ''}" onclick="event.stopPropagation()">
                            <i class="fas fa-bolt mr-1"></i> Actions
                        </button>
                    </div>
                </div>
            </div>
        `;
    }
    
    function attachCourseCardListeners() {
        // Remove existing listeners first to prevent duplicates
        document.querySelectorAll('.view-details-btn').forEach(btn => {
            btn.replaceWith(btn.cloneNode(true));
        });
        
        document.querySelectorAll('.quick-actions-btn').forEach(btn => {
            btn.replaceWith(btn.cloneNode(true));
        });
        
        // Attach new listeners
        document.querySelectorAll('.view-details-btn').forEach(btn => {
            btn.addEventListener('click', function(e) {
                e.stopPropagation();
                const courseId = this.dataset.courseId;
                if (courseId) {
                    viewCourseDetails(courseId);
                }
            });
        });
        
        document.querySelectorAll('.quick-actions-btn').forEach(btn => {
            btn.addEventListener('click', function(e) {
                e.stopPropagation();
                const courseId = this.dataset.courseId;
                if (courseId) {
                    showQuickActions(courseId);
                }
            });
        });
        
        // Course card clicks
        document.querySelectorAll('.course-card').forEach(card => {
            card.addEventListener('click', function() {
                const courseId = this.dataset.courseId;
                if (courseId) {
                    viewCourseDetails(courseId);
                }
            });
        });
    }
    
    function filterCourses() {
        const searchTerm = searchCourses?.value?.toLowerCase() || '';
        const selectedStatus = statusFilter?.value || '';
        
        filteredCourses = allCourses.filter(course => {
            const matchesSearch = !searchTerm || 
                (course.course_name && course.course_name.toLowerCase().includes(searchTerm)) ||
                (course.course_code && course.course_code.toLowerCase().includes(searchTerm));
            
            const matchesStatus = !selectedStatus || 
                course.enrollment_status === selectedStatus;
            
            return matchesSearch && matchesStatus;
        });
        
        displayCourses();
        updateStats();
    }
    
    function updateStats() {
        const totalCourses = filteredCourses.length;
        const atRiskCourses = filteredCourses.filter(c => 
            ['C-', 'D+', 'D', 'D-', 'F'].includes(c.predicted_grade) || 
            (c.attendance_rate && c.attendance_rate < 60)
        ).length;
        
        if (totalCoursesCount) totalCoursesCount.textContent = totalCourses;
        if (atRiskCoursesCount) atRiskCoursesCount.textContent = atRiskCourses;
    }
    
    function updateDashboardStats() {
        if (currentGPA) currentGPA.textContent = dashboardSummary.gpa || '-';
        if (overallAttendance) overallAttendance.textContent = `${Math.round(dashboardSummary.attendance_rate || 0)}%`;
    }
    
    function updateProgressCharts() {
        try {
            // Update attendance trend (safer)
            updateAttendanceTrend();
            
            // Update grade chart with error handling
            const ctx = document.getElementById('gradeChart');
            if (ctx && typeof Chart !== 'undefined' && allCourses.length > 0) {
                updateGradeChart();
            }
        } catch (error) {
            console.error('Error updating charts:', error);
        }
    }
    
    function updateGradeChart() {
        try {
            const ctx = document.getElementById('gradeChart');
            if (!ctx) return;
            
            // Destroy existing chart first
            if (gradeChart) {
                gradeChart.destroy();
                gradeChart = null;
            }
            
            // Calculate grade distribution
            const gradeCategories = {
                'A (90-100)': 0,
                'B (80-89)': 0,
                'C (70-79)': 0,
                'D (60-69)': 0,
                'F (0-59)': 0
            };
            
            allCourses.forEach(course => {
                const grade = course.predicted_grade;
                if (['A+', 'A', 'A-'].includes(grade)) gradeCategories['A (90-100)']++;
                else if (['B+', 'B', 'B-'].includes(grade)) gradeCategories['B (80-89)']++;
                else if (['C+', 'C', 'C-'].includes(grade)) gradeCategories['C (70-79)']++;
                else if (['D+', 'D', 'D-'].includes(grade)) gradeCategories['D (60-69)']++;
                else if (grade === 'F') gradeCategories['F (0-59)']++;
            });
            
            const labels = Object.keys(gradeCategories);
            const data = Object.values(gradeCategories);
            
            // Only create chart if we have data
            const hasData = data.some(count => count > 0);
            if (!hasData) return;
            
            gradeChart = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: labels,
                    datasets: [{
                        data: data,
                        backgroundColor: [
                            '#10B981', // Green for A
                            '#3B82F6', // Blue for B  
                            '#F59E0B', // Yellow for C
                            '#EF4444', // Red for D
                            '#DC2626'  // Dark red for F
                        ],
                        borderWidth: 2,
                        borderColor: '#fff'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom',
                            labels: {
                                font: {
                                    size: 12
                                }
                            }
                        }
                    }
                }
            });
        } catch (error) {
            console.error('Error creating grade chart:', error);
        }
    }
    
    function updateAttendanceTrend() {
        if (!attendanceTrend) return;
        
        try {
            const html = allCourses.slice(0, 5).map(course => {
                const rate = course.attendance_rate || 0;
                const color = rate >= 80 ? 'bg-green-500' :
                             rate >= 60 ? 'bg-yellow-500' : 'bg-red-500';
                
                return `
                    <div class="flex items-center justify-between p-2 bg-gray-50 rounded">
                        <span class="text-sm font-medium">${course.course_code || 'N/A'}</span>
                        <div class="flex items-center space-x-2">
                            <div class="w-16 h-2 bg-gray-200 rounded-full">
                                <div class="${color} h-2 rounded-full" style="width: ${rate}%"></div>
                            </div>
                            <span class="text-sm text-gray-600">${Math.round(rate)}%</span>
                        </div>
                    </div>
                `;
            }).join('');
            
            attendanceTrend.innerHTML = html || '<p class="text-gray-500 text-sm">No attendance data</p>';
        } catch (error) {
            console.error('Error updating attendance trend:', error);
            attendanceTrend.innerHTML = '<p class="text-gray-500 text-sm">Error loading attendance data</p>';
        }
    }
    
    async function viewCourseDetails(courseId) {
        try {
            const course = allCourses.find(c => c.course_id == courseId);
            if (!course) {
                showError('Course not found');
                return;
            }
            
            modalCourseTitle.textContent = `${course.course_code || 'N/A'} - ${course.course_name || 'Course'}`;
            
            courseModalContent.innerHTML = `
                <div class="space-y-6">
                    <!-- Course Overview -->
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div>
                            <h4 class="font-semibold text-gray-900 mb-3">Course Information</h4>
                            <div class="space-y-2 text-sm">
                                <p><strong>Course Code:</strong> ${course.course_code || 'N/A'}</p>
                                <p><strong>Credits:</strong> ${course.credits || 'N/A'}</p>
                                <p><strong>Section:</strong> ${course.section || 'N/A'}</p>
                                <p><strong>Instructor:</strong> ${course.instructor_name || 'TBA'}</p>
                                <p><strong>Schedule:</strong> ${course.meeting_pattern || 'TBA'}</p>
                                <p><strong>Location:</strong> ${course.location || 'TBA'}</p>
                            </div>
                        </div>
                        <div>
                            <h4 class="font-semibold text-gray-900 mb-3">Academic Performance</h4>
                            <div class="space-y-2 text-sm">
                                <p><strong>Current Grade:</strong> ${course.current_grade || 'N/A'}</p>
                                <p><strong>Predicted Grade:</strong> ${course.predicted_grade || 'N/A'}</p>
                                <p><strong>Attendance Rate:</strong> ${Math.round(course.attendance_rate || 0)}%</p>
                                <p><strong>Enrollment Status:</strong> ${course.enrollment_status || 'Enrolled'}</p>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Performance Metrics -->
                    <div>
                        <h4 class="font-semibold text-gray-900 mb-3">Performance Overview</h4>
                        <div class="grid grid-cols-3 gap-4">
                            <div class="bg-blue-50 p-4 rounded-lg text-center">
                                <div class="text-2xl font-bold text-blue-600">${Math.round(course.attendance_rate || 0)}%</div>
                                <div class="text-sm text-gray-600">Attendance</div>
                            </div>
                            <div class="bg-green-50 p-4 rounded-lg text-center">
                                <div class="text-2xl font-bold text-green-600">${course.current_grade || 'N/A'}</div>
                                <div class="text-sm text-gray-600">Current Grade</div>
                            </div>
                            <div class="bg-purple-50 p-4 rounded-lg text-center">
                                <div class="text-2xl font-bold text-purple-600">${course.predicted_grade || 'N/A'}</div>
                                <div class="text-sm text-gray-600">Predicted Grade</div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Quick Links -->
                    <div class="grid grid-cols-2 gap-3 pt-4 border-t">
                        <button onclick="navigateToPage('attendance.html?course=${course.course_id}')" 
                                class="bg-green-600 text-white py-2 px-4 rounded hover:bg-green-700">
                            <i class="fas fa-calendar-check mr-2"></i>View Attendance
                        </button>
                        <button onclick="navigateToPage('assessments.html?course=${course.course_id}')" 
                                class="bg-blue-600 text-white py-2 px-4 rounded hover:bg-blue-700">
                            <i class="fas fa-clipboard-check mr-2"></i>View Assessments
                        </button>
                        <button onclick="navigateToPage('grades.html?course=${course.course_id}')" 
                                class="bg-purple-600 text-white py-2 px-4 rounded hover:bg-purple-700">
                            <i class="fas fa-chart-line mr-2"></i>View Grades
                        </button>
                        <button onclick="navigateToPage('predictions.html?course=${course.course_id}')" 
                                class="bg-orange-600 text-white py-2 px-4 rounded hover:bg-orange-700">
                            <i class="fas fa-crystal-ball mr-2"></i>View Predictions
                        </button>
                    </div>
                </div>
            `;
            
            courseModal.classList.remove('hidden');
            
        } catch (error) {
            console.error('Error viewing course details:', error);
            showError('Failed to load course details');
        }
    }
    
    function showQuickActions(courseId) {
        const course = allCourses.find(c => c.course_id == courseId);
        if (!course) return;
        
        quickActionsContent.innerHTML = `
            <button onclick="navigateToPage('attendance.html?course=${course.course_id}')" 
                    class="w-full text-left p-3 hover:bg-gray-50 rounded border">
                <i class="fas fa-calendar-check text-green-600 mr-3"></i>
                <span class="font-medium">View Attendance</span>
                <p class="text-sm text-gray-600 mt-1">Check your attendance record</p>
            </button>
            <button onclick="navigateToPage('assessments.html?course=${course.course_id}')" 
                    class="w-full text-left p-3 hover:bg-gray-50 rounded border">
                <i class="fas fa-clipboard-check text-blue-600 mr-3"></i>
                <span class="font-medium">View Assessments</span>
                <p class="text-sm text-gray-600 mt-1">See assignments and grades</p>
            </button>
            <button onclick="navigateToPage('predictions.html?course=${course.course_id}')" 
                    class="w-full text-left p-3 hover:bg-gray-50 rounded border">
                <i class="fas fa-crystal-ball text-purple-600 mr-3"></i>
                <span class="font-medium">Grade Predictions</span>
                <p class="text-sm text-gray-600 mt-1">View performance predictions</p>
            </button>
            <button onclick="window.location.href='mailto:${course.instructor_email || ''}'" 
                    class="w-full text-left p-3 hover:bg-gray-50 rounded border">
                <i class="fas fa-envelope text-orange-600 mr-3"></i>
                <span class="font-medium">Contact Instructor</span>
                <p class="text-sm text-gray-600 mt-1">Send email to ${course.instructor_name || 'instructor'}</p>
            </button>
        `;
        
        quickActionsModal.classList.remove('hidden');
    }
    
    // Helper function for navigation
    function navigateToPage(url) {
        window.location.href = url;
    }
    
    function showLoading() {
        if (coursesContainer) {
            coursesContainer.innerHTML = `
                <div class="col-span-full text-center py-8">
                    <div class="inline-flex items-center px-4 py-2 text-gray-600">
                        <i class="fas fa-spinner fa-spin mr-2"></i>
                        Loading courses...
                    </div>
                </div>
            `;
        }
    }
    
    function showEmptyState() {
        if (coursesContainer) coursesContainer.innerHTML = '';
        if (emptyState) emptyState.classList.remove('hidden');
    }
    
    function hideEmptyState() {
        if (emptyState) emptyState.classList.add('hidden');
    }
    
    function showError(message) {
        showNotification(message, 'error');
    }
    
    function showNotification(message, type = 'info') {
        const bgColor = type === 'error' ? 'bg-red-500' : 
                       type === 'success' ? 'bg-green-500' : 'bg-blue-500';
        
        const toast = document.createElement('div');
        toast.className = `fixed top-4 right-4 ${bgColor} text-white px-4 py-2 rounded shadow-lg z-50 transition-opacity duration-300`;
        toast.innerHTML = `
            <div class="flex items-center">
                <i class="fas fa-${type === 'error' ? 'exclamation-circle' : 'info-circle'} mr-2"></i>
                ${message}
            </div>
        `;
        
        document.body.appendChild(toast);
        
        // Fade out and remove
        setTimeout(() => {
            toast.style.opacity = '0';
            setTimeout(() => {
                if (toast.parentNode) {
                    toast.parentNode.removeChild(toast);
                }
            }, 300);
        }, 4000);
    }
});

// Global function for navigation (needed for onclick handlers)
window.navigateToPage = function(url) {
    window.location.href = url;
};