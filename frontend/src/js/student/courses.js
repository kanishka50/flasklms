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
    let isLoading = false; // Prevent multiple simultaneous loads
    
    // Initialize
    init();
    
    function init() {
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
        
        // Setup event listeners
        setupEventListeners();
        
        // Load data with delay to ensure DOM is ready
        setTimeout(() => {
            loadAllData();
        }, 100);
    }
    
    function setupEventListeners() {
        // Logout
        logoutBtn?.addEventListener('click', function() {
            authApi.logout();
            window.location.href = '../login.html';
        });
        
        // Refresh
        refreshBtn?.addEventListener('click', function() {
            if (!isLoading) {
                loadAllData();
            }
        });
        
        // Enroll button
        enrollBtn?.addEventListener('click', function() {
            alert('Course enrollment feature coming soon!');
        });
        
        // Search and filters - debounced
        let searchTimeout;
        searchCourses?.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                filterCourses();
            }, 300);
        });
        
        termFilter?.addEventListener('change', function() {
            if (!isLoading) {
                loadCourses();
            }
        });
        
        statusFilter?.addEventListener('change', function() {
            filterCourses();
        });
        
        // Close modals
        closeCourseModal?.addEventListener('click', function() {
            courseModal.classList.add('hidden');
        });
        
        closeQuickActionsModal?.addEventListener('click', function() {
            quickActionsModal.classList.add('hidden');
        });
        
        // Close modal on backdrop click
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
    
    async function loadAllData() {
        if (isLoading) return; // Prevent multiple loads
        
        try {
            isLoading = true;
            showLoading();
            
            // Load dashboard summary first
            await loadDashboardSummary();
            
            // Then load courses
            await loadCourses();
            
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
                updateDashboardStats();
            }
        } catch (error) {
            console.error('Error loading dashboard summary:', error);
            // Continue without dashboard data
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
                displayCourses();
                updateStats();
                // Safely update charts with delay
                setTimeout(() => {
                    updateProgressChartsSafely();
                }, 100);
            } else {
                allCourses = [];
                filteredCourses = [];
                displayCourses();
            }
        } catch (error) {
            console.error('Error loading courses:', error);
            showError('Failed to load courses');
        }
    }
    
    function displayCourses() {
        if (!filteredCourses || filteredCourses.length === 0) {
            showEmptyState();
            return;
        }
        
        hideEmptyState();
        const html = filteredCourses.map(course => createCourseCard(course)).join('');
        coursesContainer.innerHTML = html;
        
        // Add click listeners
        attachCourseCardListeners();
    }
    
    function createCourseCard(course) {
        const attendanceRate = course.attendance_rate || 0;
        const predictedGrade = course.predicted_grade || 'N/A';
        const currentGrade = course.current_grade || 'N/A';
        
        // Determine colors and status
        const attendanceColor = attendanceRate >= 80 ? 'text-green-600' :
                               attendanceRate >= 60 ? 'text-yellow-600' : 'text-red-600';
        
        const gradeColor = ['A', 'B'].includes(predictedGrade) ? 'text-green-600' :
                          predictedGrade === 'C' ? 'text-yellow-600' : 
                          ['D', 'F'].includes(predictedGrade) ? 'text-red-600' : 'text-gray-600';
        
        const statusColor = course.enrollment_status === 'completed' ? 
            'bg-gray-100 text-gray-800' : 'bg-green-100 text-green-800';
        
        const isAtRisk = ['D', 'F'].includes(predictedGrade) || attendanceRate < 60;
        
        return `
            <div class="bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow duration-300 course-card" 
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
                                data-course-id="${course.course_id || ''}">
                            <i class="fas fa-eye mr-1"></i> Details
                        </button>
                        <button class="flex-1 bg-green-600 text-white py-2 px-3 rounded text-sm hover:bg-green-700 quick-actions-btn"
                                data-course-id="${course.course_id || ''}">
                            <i class="fas fa-bolt mr-1"></i> Actions
                        </button>
                    </div>
                </div>
            </div>
        `;
    }
    
    function attachCourseCardListeners() {
        // View details buttons
        document.querySelectorAll('.view-details-btn').forEach(btn => {
            btn.addEventListener('click', function(e) {
                e.stopPropagation();
                const courseId = this.dataset.courseId;
                if (courseId) {
                    viewCourseDetails(courseId);
                }
            });
        });
        
        // Quick actions buttons
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
            ['D', 'F'].includes(c.predicted_grade) || (c.attendance_rate && c.attendance_rate < 60)
        ).length;
        
        if (totalCoursesCount) totalCoursesCount.textContent = totalCourses;
        if (atRiskCoursesCount) atRiskCoursesCount.textContent = atRiskCourses;
    }
    
    function updateDashboardStats() {
        if (currentGPA) currentGPA.textContent = dashboardSummary.gpa || '-';
        if (overallAttendance) overallAttendance.textContent = `${Math.round(dashboardSummary.attendance_rate || 0)}%`;
    }
    
    function updateProgressChartsSafely() {
        try {
            // Update attendance trend (safer)
            updateAttendanceTrend();
            
            // Update grade chart with error handling
            const ctx = document.getElementById('gradeChart');
            if (ctx && typeof Chart !== 'undefined' && allCourses.length > 0) {
                updateGradeChartSafely();
            } else {
                console.log('Chart.js not loaded or no courses data');
            }
        } catch (error) {
            console.error('Error updating charts:', error);
        }
    }
    
    function updateGradeChartSafely() {
        try {
            const ctx = document.getElementById('gradeChart');
            if (!ctx) return;
            
            // Calculate grade distribution
            const grades = ['A', 'B', 'C', 'D', 'F'];
            const gradeData = grades.map(grade => 
                allCourses.filter(c => c.predicted_grade === grade).length
            );
            
            // Destroy existing chart
            if (gradeChart) {
                gradeChart.destroy();
                gradeChart = null;
            }
            
            // Only create chart if we have data
            const hasData = gradeData.some(count => count > 0);
            if (!hasData) {
                ctx.getContext('2d').clearRect(0, 0, ctx.width, ctx.height);
                return;
            }
            
            gradeChart = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: grades,
                    datasets: [{
                        data: gradeData,
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
                            position: 'bottom'
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
            const course = allCourses.find(c => c.course_id === courseId);
            if (!course) {
                showError('Course not found');
                return;
            }
            
            modalCourseTitle.textContent = `${course.course_code || 'N/A'} - ${course.course_name || 'Course'}`;
            
            // Display course details modal
            courseModalContent.innerHTML = `
                <div class="space-y-6">
                    <!-- Course Overview -->
                    <div class="grid grid-cols-2 gap-6">
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
                        <button onclick="window.location.href='attendance.html?course=${course.course_id}'" 
                                class="bg-green-600 text-white py-2 px-4 rounded hover:bg-green-700">
                            <i class="fas fa-calendar-check mr-2"></i>View Attendance
                        </button>
                        <button onclick="window.location.href='assessments.html?course=${course.course_id}'" 
                                class="bg-blue-600 text-white py-2 px-4 rounded hover:bg-blue-700">
                            <i class="fas fa-clipboard-check mr-2"></i>View Assessments
                        </button>
                        <button onclick="window.location.href='grades.html?course=${course.course_id}'" 
                                class="bg-purple-600 text-white py-2 px-4 rounded hover:bg-purple-700">
                            <i class="fas fa-chart-line mr-2"></i>View Grades
                        </button>
                        <button onclick="window.location.href='predictions.html?course=${course.course_id}'" 
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
        const course = allCourses.find(c => c.course_id === courseId);
        if (!course) return;
        
        quickActionsContent.innerHTML = `
            <button onclick="window.location.href='attendance.html?course=${course.course_id}'" 
                    class="w-full text-left p-3 hover:bg-gray-50 rounded border">
                <i class="fas fa-calendar-check text-green-600 mr-3"></i>
                <span class="font-medium">View Attendance</span>
                <p class="text-sm text-gray-600 mt-1">Check your attendance record</p>
            </button>
            <button onclick="window.location.href='assessments.html?course=${course.course_id}'" 
                    class="w-full text-left p-3 hover:bg-gray-50 rounded border">
                <i class="fas fa-clipboard-check text-blue-600 mr-3"></i>
                <span class="font-medium">View Assessments</span>
                <p class="text-sm text-gray-600 mt-1">See assignments and grades</p>
            </button>
            <button onclick="window.location.href='predictions.html?course=${course.course_id}'" 
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
        const toast = document.createElement('div');
        toast.className = 'fixed top-4 right-4 bg-red-500 text-white px-4 py-2 rounded shadow-lg z-50';
        toast.innerHTML = `
            <div class="flex items-center">
                <i class="fas fa-exclamation-circle mr-2"></i>
                ${message}
            </div>
        `;
        
        document.body.appendChild(toast);
        
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 5000);
    }
});