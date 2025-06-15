// Admin Course Management JavaScript
document.addEventListener('DOMContentLoaded', function() {
    // Elements
    const usernameElement = document.getElementById('username');
    const logoutBtn = document.getElementById('logoutBtn');
    const addCourseBtn = document.getElementById('addCourseBtn');
    
    // Statistics elements
    const totalCourses = document.getElementById('totalCourses');
    const activeOfferings = document.getElementById('activeOfferings');
    const totalEnrollments = document.getElementById('totalEnrollments');
    const avgCredits = document.getElementById('avgCredits');
    
    // Table elements
    const coursesTableBody = document.getElementById('coursesTableBody');
    const searchInput = document.getElementById('searchInput');
    const searchBtn = document.getElementById('searchBtn');
    
    // Pagination elements
    const startRecord = document.getElementById('startRecord');
    const endRecord = document.getElementById('endRecord');
    const totalRecords = document.getElementById('totalRecords');
    const prevPage = document.getElementById('prevPage');
    const nextPage = document.getElementById('nextPage');
    
    // Modal elements
    const courseModal = document.getElementById('courseModal');
    const modalTitle = document.getElementById('modalTitle');
    const closeModal = document.getElementById('closeModal');
    const cancelBtn = document.getElementById('cancelBtn');
    const courseForm = document.getElementById('courseForm');
    
    // State
    let courses = [];
    let currentPage = 1;
    let totalPages = 1;
    let searchQuery = '';
    
    // Initialize
    init();
    
    function init() {
        // Check authentication
        if (!authApi.isLoggedIn()) {
            window.location.href = '../login.html';
            return;
        }
        
        // Check if user is admin
        const user = authApi.getCurrentUser();
        if (user.user_type !== 'admin') {
            alert('Access denied. Admin privileges required.');
            window.location.href = '../login.html';
            return;
        }
        
        // Display username
        if (user) {
            usernameElement.textContent = user.username;
        }
        
        // Set up event listeners
        setupEventListeners();
        
        // Load initial data
        loadStatistics();
        loadCourses();
    }
    
    function setupEventListeners() {
        // Logout
        logoutBtn.addEventListener('click', function() {
            if (confirm('Are you sure you want to logout?')) {
                authApi.logout();
            }
        });
        
        // Add course
        addCourseBtn.addEventListener('click', function() {
            openCourseModal();
        });
        
        // Search
        searchBtn.addEventListener('click', performSearch);
        searchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                performSearch();
            }
        });
        
        // Pagination
        prevPage.addEventListener('click', function() {
            if (currentPage > 1) {
                currentPage--;
                loadCourses();
            }
        });
        
        nextPage.addEventListener('click', function() {
            if (currentPage < totalPages) {
                currentPage++;
                loadCourses();
            }
        });
        
        // Modal
        closeModal.addEventListener('click', closeCourseModal);
        cancelBtn.addEventListener('click', closeCourseModal);
        courseForm.addEventListener('submit', handleCourseSubmit);
        
        // Close modal on outside click
        courseModal.addEventListener('click', function(e) {
            if (e.target === courseModal) {
                closeCourseModal();
            }
        });
    }
    
    async function loadStatistics() {
        try {
            // Load course statistics
            const stats = await adminApi.getStatistics();
            
            if (stats.status === 'success' && stats.data) {
                // Update statistics display
                totalCourses.textContent = stats.data.total_courses || '-';
                activeOfferings.textContent = stats.data.active_courses || '-';
                totalEnrollments.textContent = stats.data.total_enrollments || '-';
                
                // Calculate average credits (demo value)
                avgCredits.textContent = '3.5';
            }
        } catch (error) {
            console.error('Error loading statistics:', error);
            
            // Show demo values
            totalCourses.textContent = '25';
            activeOfferings.textContent = '18';
            totalEnrollments.textContent = '456';
            avgCredits.textContent = '3.5';
        }
    }
    
    async function loadCourses() {
        try {
            const params = {
                page: currentPage,
                limit: 10,
                search: searchQuery
            };
            
            const response = await adminApi.getCourses(params);
            
            if (response.status === 'success' && response.data) {
                courses = response.data.courses;
                currentPage = response.data.current_page;
                totalPages = response.data.total_pages;
                
                displayCourses(courses);
                updatePagination(response.data);
            }
        } catch (error) {
            console.error('Error loading courses:', error);
            
            // Show demo data
            const demoCourses = [
                {
                    course_id: 1,
                    course_code: 'CS101',
                    course_name: 'Introduction to Computer Science',
                    credits: 3,
                    description: 'Basic concepts of computer science',
                    active_offerings: 2
                },
                {
                    course_id: 2,
                    course_code: 'CS201',
                    course_name: 'Data Structures and Algorithms',
                    credits: 4,
                    description: 'Fundamental data structures and algorithms',
                    active_offerings: 1
                },
                {
                    course_id: 3,
                    course_code: 'MATH101',
                    course_name: 'Calculus I',
                    credits: 4,
                    description: 'Introduction to differential and integral calculus',
                    active_offerings: 3
                }
            ];
            displayCourses(demoCourses);
            updatePagination({ total: 3, current_page: 1, per_page: 10 });
        }
    }
    
    function displayCourses(courses) {
    if (!courses || courses.length === 0) {
        coursesTableBody.innerHTML = `
            <tr>
                <td colspan="5" class="px-6 py-4 text-center text-gray-500">
                    No courses found
                </td>
            </tr>
        `;
        return;
    }
    
    const html = courses.map(course => {
        // Calculate total enrollments for this course (demo value)
        const enrollments = course.active_offerings * Math.floor(Math.random() * 30 + 10);
        
        return `
            <tr class="hover:bg-gray-50">
                <td class="px-6 py-4 whitespace-nowrap">
                    <div>
                        <div class="text-sm font-medium text-gray-900">${course.course_code}</div>
                        <div class="text-sm text-gray-500">${course.course_name}</div>
                    </div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                    <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-gray-100 text-gray-800">
                        ${course.credits} credits
                    </span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    ${course.active_offerings || 0} active
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    ${enrollments} students
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <button onclick="window.editCourse('${course.course_id}')" class="text-indigo-600 hover:text-indigo-900 mr-3">
                        <i class="fas fa-edit"></i> Edit
                    </button>
                    <button onclick="window.viewOfferings('${course.course_id}')" class="text-green-600 hover:text-green-900">
                        <i class="fas fa-list"></i> Offerings
                    </button>
                </td>
            </tr>
        `;
    }).join('');
    
    coursesTableBody.innerHTML = html;
}
    
    function updatePagination(data) {
        const start = (data.current_page - 1) * data.per_page + 1;
        const end = Math.min(data.current_page * data.per_page, data.total);
        
        startRecord.textContent = start;
        endRecord.textContent = end;
        totalRecords.textContent = data.total;
        
        // Update button states
        prevPage.disabled = currentPage === 1;
        nextPage.disabled = currentPage === totalPages;
    }
    
    function performSearch() {
        searchQuery = searchInput.value;
        currentPage = 1;
        loadCourses();
    }
    
    function openCourseModal(course = null) {
    if (course) {
        modalTitle.textContent = 'Edit Course';
        // Load course data
        document.getElementById('courseId').value = course.course_id;
        document.getElementById('modalCourseCode').value = course.course_code;
        document.getElementById('modalCourseName').value = course.course_name;
        document.getElementById('modalCredits').value = course.credits;
        document.getElementById('modalDescription').value = course.description || '';
    } else {
        modalTitle.textContent = 'Add New Course';
        courseForm.reset();
    }
    
    courseModal.classList.remove('hidden');
    }
    
    function closeCourseModal() {
        courseModal.classList.add('hidden');
        courseForm.reset();
    }
    
    async function handleCourseSubmit(e) {
        e.preventDefault();
        
        const formData = new FormData(courseForm);
        const courseId = formData.get('courseId');
        
        const courseData = {
            course_code: formData.get('courseCode'),
            course_name: formData.get('courseName'),
            credits: parseInt(formData.get('credits')),
            description: formData.get('description')
        };
        
        try {
            let response;
            if (courseId) {
                // Update existing course
                response = await adminApi.updateCourse(courseId, courseData);
            } else {
                // Create new course
                response = await adminApi.createCourse(courseData);
            }
            
            if (response.status === 'success') {
                alert(courseId ? 'Course updated successfully' : 'Course created successfully');
                closeCourseModal();
                loadCourses();
                loadStatistics();
            }
        } catch (error) {
            console.error('Error saving course:', error);
            alert('Error saving course. Please try again.');
        }
    }
    
    // Global functions for inline buttons
    window.editCourse = function(courseId) {
    // Find the course by its ID
    const course = courses.find(c => c.course_id === courseId);
    if (course) {
        openCourseModal(course);
    }
    };
    
    window.viewOfferings = function(courseId) {
    // Redirect to offerings page or show offerings modal
    alert(`View offerings for course ID: ${courseId}`);
    // In a real implementation, this would navigate to a course details page
    // window.location.href = `course-offerings.html?id=${courseId}`;
    };
    
    // Set active sidebar item
    function setActiveSidebarItem() {
        const currentPage = window.location.pathname.split('/').pop();
        const sidebarLinks = document.querySelectorAll('aside a');
        
        sidebarLinks.forEach(link => {
            if (link.getAttribute('href') === currentPage) {
                link.classList.add('bg-gray-100');
            } else {
                link.classList.remove('bg-gray-100');
            }
        });
    }
    
    setActiveSidebarItem();
});