document.addEventListener('DOMContentLoaded', function() {
    // Elements
    const usernameElement = document.getElementById('username');
    const logoutBtn = document.getElementById('logoutBtn');
    const courseFilter = document.getElementById('courseFilter');
    const riskFilter = document.getElementById('riskFilter');
    const statusFilter = document.getElementById('statusFilter');
    const searchInput = document.getElementById('searchInput');
    const clearFiltersBtn = document.getElementById('clearFiltersBtn');
    const exportBtn = document.getElementById('exportBtn');
    const loadingIndicator = document.getElementById('loadingIndicator');
    const studentsContainer = document.getElementById('studentsContainer');
    const noStudents = document.getElementById('noStudents');
    const studentsTableBody = document.getElementById('studentsTableBody');
    const studentsCount = document.getElementById('studentsCount');
    
    // Summary elements
    const totalStudents = document.getElementById('totalStudents');
    const activeStudents = document.getElementById('activeStudents');
    const atRiskStudents = document.getElementById('atRiskStudents');
    const avgAttendance = document.getElementById('avgAttendance');
    
    // State
    let allStudents = [];
    let filteredStudents = [];
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
        if (!authApi.hasRole('faculty')) {
            window.location.href = '../login.html';
            return;
        }
        
        // Display username
        const user = authApi.getCurrentUser();
        if (user) {
            usernameElement.textContent = user.username;
        }
        
        // Load data
        loadFacultyCourses();
        loadAllStudents();
        
        // Set up event listeners
        setupEventListeners();
    }
    
    function setupEventListeners() {
        // Logout
        logoutBtn.addEventListener('click', function() {
            authApi.logout();
        });
        
        // Filters
        courseFilter.addEventListener('change', filterStudents);
        riskFilter.addEventListener('change', filterStudents);
        statusFilter.addEventListener('change', filterStudents);
        searchInput.addEventListener('input', debounce(filterStudents, 300));
        
        // Clear filters
        clearFiltersBtn.addEventListener('click', function() {
            courseFilter.value = '';
            riskFilter.value = '';
            statusFilter.value = '';
            searchInput.value = '';
            filterStudents();
        });
        
        // Export
        exportBtn.addEventListener('click', exportToCSV);
    }
    
    async function loadFacultyCourses() {
        try {
            const response = await apiClient.get('faculty/courses');
            if (response.status === 'success' && response.data.courses) {
                coursesList = response.data.courses;
                populateCourseFilter();
            }
        } catch (error) {
            console.error('Error loading courses:', error);
        }
    }
    
    async function loadAllStudents() {
        try {
            showLoading(true);
            
            allStudents = [];
            
            // Load students for each course with detailed information
            for (const course of coursesList) {
                try {
                    // Get students for this course
                    const studentsResponse = await apiClient.get(`faculty/students?offering_id=${course.offering_id}`);
                    if (studentsResponse.status === 'success' && studentsResponse.data.students) {
                        
                        // Get attendance summary for this course
                        let attendanceData = {};
                        try {
                            const attendanceResponse = await apiClient.get(`faculty/attendance/summary/${course.offering_id}`);
                            if (attendanceResponse.status === 'success' && attendanceResponse.data.summary) {
                                attendanceResponse.data.summary.forEach(record => {
                                    attendanceData[record.student_id] = record;
                                });
                            }
                        } catch (error) {
                            console.error(`Error loading attendance for course ${course.course_code}:`, error);
                        }
                        
                        // Combine student data with attendance and course info
                        studentsResponse.data.students.forEach(student => {
                            const attendance = attendanceData[student.student_id] || {
                                attendance_rate: 0,
                                present_count: 0,
                                total_classes: 0
                            };
                            
                            allStudents.push({
                                ...student,
                                course_code: course.course_code,
                                course_name: course.course_name,
                                offering_id: course.offering_id,
                                section: course.section,
                                attendance_rate: attendance.attendance_rate,
                                present_count: attendance.present_count,
                                total_classes: attendance.total_classes,
                                // Mock data for risk level (replace with actual prediction data)
                                risk_level: calculateRiskLevel(attendance.attendance_rate, student.gpa),
                                predicted_grade: calculatePredictedGrade(attendance.attendance_rate, student.gpa)
                            });
                        });
                    }
                } catch (error) {
                    console.error(`Error loading students for course ${course.course_code}:`, error);
                }
            }
            
            updateSummaryStats();
            filterStudents();
            
        } catch (error) {
            console.error('Error loading students:', error);
            showError('Failed to load students. Please refresh the page.');
        } finally {
            showLoading(false);
        }
    }
    
    function populateCourseFilter() {
        courseFilter.innerHTML = '<option value="">All Courses</option>';
        
        coursesList.forEach(course => {
            const option = document.createElement('option');
            option.value = course.offering_id;
            option.textContent = `${course.course_code} - ${course.course_name}`;
            courseFilter.appendChild(option);
        });
    }
    
    function filterStudents() {
        const courseFilterValue = courseFilter.value;
        const riskFilterValue = riskFilter.value;
        const statusFilterValue = statusFilter.value;
        const searchValue = searchInput.value.toLowerCase();
        
        filteredStudents = allStudents.filter(student => {
            // Course filter
            if (courseFilterValue && student.offering_id != courseFilterValue) {
                return false;
            }
            
            // Risk filter
            if (riskFilterValue && student.risk_level !== riskFilterValue) {
                return false;
            }
            
            // Status filter
            if (statusFilterValue && student.status !== statusFilterValue) {
                return false;
            }
            
            // Search filter
            if (searchValue) {
                const searchText = `${student.first_name} ${student.last_name} ${student.student_id}`.toLowerCase();
                if (!searchText.includes(searchValue)) {
                    return false;
                }
            }
            
            return true;
        });
        
        displayStudents(filteredStudents);
        updateFilteredCount();
    }
    
    function displayStudents(students) {
        if (!students.length) {
            showNoStudents();
            return;
        }
        
        studentsTableBody.innerHTML = '';
        
        students.forEach(student => {
            const row = createStudentRow(student);
            studentsTableBody.appendChild(row);
        });
        
        studentsContainer.classList.remove('hidden');
        noStudents.classList.add('hidden');
    }
    
    function createStudentRow(student) {
        const row = document.createElement('tr');
        row.className = 'hover:bg-gray-50';
        
        const riskBadge = getRiskBadge(student.risk_level);
        const attendanceBadge = getAttendanceBadge(student.attendance_rate);
        const gradeBadge = getGradeBadge(student.predicted_grade);
        
        row.innerHTML = `
            <td class="px-6 py-4 whitespace-nowrap">
                <div class="flex items-center">
                    <div class="w-10 h-10 bg-gray-300 rounded-full flex items-center justify-center text-gray-600 font-medium text-sm">
                        ${student.first_name[0]}${student.last_name[0]}
                    </div>
                    <div class="ml-4">
                        <div class="text-sm font-medium text-gray-900">${student.first_name} ${student.last_name}</div>
                        <div class="text-sm text-gray-500">ID: ${student.student_id}</div>
                    </div>
                </div>
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
                <div class="text-sm text-gray-900">${student.course_code}</div>
                <div class="text-sm text-gray-500">Section ${student.section}</div>
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
                <div class="flex items-center">
                    <div class="text-sm font-medium text-gray-900">${student.attendance_rate.toFixed(1)}%</div>
                    ${attendanceBadge}
                </div>
                <div class="text-sm text-gray-500">${student.present_count}/${student.total_classes} classes</div>
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
                <div class="flex items-center">
                    <div class="text-sm font-medium text-gray-900">${student.gpa || 'N/A'}</div>
                    ${gradeBadge}
                </div>
                <div class="text-sm text-gray-500">Predicted: ${student.predicted_grade}</div>
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
                ${riskBadge}
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm space-x-2">
                <a href="student-detail.html?student_id=${student.student_id}&offering_id=${student.offering_id}" 
                   class="text-blue-600 hover:text-blue-900">View Details</a>
                <a href="attendance.html?course=${student.offering_id}" 
                   class="text-green-600 hover:text-green-900">Attendance</a>
                <a href="assessments.html?course=${student.offering_id}" 
                   class="text-purple-600 hover:text-purple-900">Assessments</a>
            </td>
        `;
        
        return row;
    }
    
    function updateSummaryStats() {
        const total = allStudents.length;
        const active = allStudents.filter(s => s.status === 'active').length;
        const atRisk = allStudents.filter(s => s.risk_level === 'high' || s.risk_level === 'medium').length;
        
        // Calculate average attendance
        const avgAtt = total > 0 ? 
            allStudents.reduce((sum, s) => sum + s.attendance_rate, 0) / total : 0;
        
        totalStudents.textContent = total;
        activeStudents.textContent = active;
        atRiskStudents.textContent = atRisk;
        avgAttendance.textContent = avgAtt.toFixed(1) + '%';
    }
    
    function updateFilteredCount() {
        const count = filteredStudents.length;
        const total = allStudents.length;
        
        if (count === total) {
            studentsCount.textContent = `Showing all ${total} students`;
        } else {
            studentsCount.textContent = `Showing ${count} of ${total} students`;
        }
    }
    
    function getRiskBadge(riskLevel) {
        const badges = {
            'low': '<span class="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-800">Low Risk</span>',
            'medium': '<span class="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-yellow-100 text-yellow-800">Medium Risk</span>',
            'high': '<span class="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-red-100 text-red-800">High Risk</span>'
        };
        return badges[riskLevel] || '<span class="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-gray-100 text-gray-800">Unknown</span>';
    }
    
    function getAttendanceBadge(rate) {
        if (rate >= 90) return '<span class="ml-2 inline-flex px-1 py-0.5 text-xs rounded-full bg-green-100 text-green-800">Excellent</span>';
        if (rate >= 80) return '<span class="ml-2 inline-flex px-1 py-0.5 text-xs rounded-full bg-blue-100 text-blue-800">Good</span>';
        if (rate >= 70) return '<span class="ml-2 inline-flex px-1 py-0.5 text-xs rounded-full bg-yellow-100 text-yellow-800">Warning</span>';
        return '<span class="ml-2 inline-flex px-1 py-0.5 text-xs rounded-full bg-red-100 text-red-800">Poor</span>';
    }
    
    function getGradeBadge(grade) {
        const badges = {
            'A': '<span class="ml-2 inline-flex px-1 py-0.5 text-xs rounded-full bg-green-100 text-green-800">A</span>',
            'B': '<span class="ml-2 inline-flex px-1 py-0.5 text-xs rounded-full bg-blue-100 text-blue-800">B</span>',
            'C': '<span class="ml-2 inline-flex px-1 py-0.5 text-xs rounded-full bg-yellow-100 text-yellow-800">C</span>',
            'D': '<span class="ml-2 inline-flex px-1 py-0.5 text-xs rounded-full bg-orange-100 text-orange-800">D</span>',
            'F': '<span class="ml-2 inline-flex px-1 py-0.5 text-xs rounded-full bg-red-100 text-red-800">F</span>'
        };
        return badges[grade] || '';
    }
    
    function calculateRiskLevel(attendanceRate, gpa) {
        // Simple risk calculation based on attendance and GPA
        const gpaScore = gpa ? parseFloat(gpa) : 2.0;
        
        if (attendanceRate < 70 || gpaScore < 2.0) return 'high';
        if (attendanceRate < 85 || gpaScore < 3.0) return 'medium';
        return 'low';
    }
    
    function calculatePredictedGrade(attendanceRate, gpa) {
        // Simple grade prediction
        const gpaScore = gpa ? parseFloat(gpa) : 2.0;
        const combined = (attendanceRate / 100 * 0.3) + (gpaScore / 4.0 * 0.7);
        
        if (combined >= 0.9) return 'A';
        if (combined >= 0.8) return 'B';
        if (combined >= 0.7) return 'C';
        if (combined >= 0.6) return 'D';
        return 'F';
    }
    
    function exportToCSV() {
        let csv = 'Student ID,Name,Course,Attendance Rate,Present Count,Total Classes,GPA,Predicted Grade,Risk Level,Status\n';
        
        filteredStudents.forEach(student => {
            csv += `"${student.student_id}","${student.first_name} ${student.last_name}","${student.course_code}","${student.attendance_rate.toFixed(1)}%","${student.present_count}","${student.total_classes}","${student.gpa || 'N/A'}","${student.predicted_grade}","${student.risk_level}","${student.status}"\n`;
        });
        
        // Download CSV
        const blob = new Blob([csv], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `students_${new Date().toISOString().split('T')[0]}.csv`;
        a.click();
        window.URL.revokeObjectURL(url);
    }
    
    function showLoading(show) {
        if (show) {
            loadingIndicator.classList.remove('hidden');
            studentsContainer.classList.add('hidden');
            noStudents.classList.add('hidden');
        } else {
            loadingIndicator.classList.add('hidden');
        }
    }
    
    function showNoStudents() {
        studentsContainer.classList.add('hidden');
        noStudents.classList.remove('hidden');
    }
    
    function showError(message) {
        console.error(message);
        alert(message);
    }
    
    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
});