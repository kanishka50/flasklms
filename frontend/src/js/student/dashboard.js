document.addEventListener('DOMContentLoaded', function() {
    // Get elements
    const usernameElement = document.getElementById('username');
    const logoutBtn = document.getElementById('logoutBtn');
    const coursesList = document.getElementById('coursesList');
    const predictionsList = document.getElementById('predictionsList');
    
    // Dashboard summary elements (add these IDs to your HTML)
    const gpaElement = document.getElementById('currentGPA');
    const attendanceElement = document.getElementById('attendanceRate');
    const assessmentsElement = document.getElementById('upcomingAssessments');
    
    // Display username
    const user = authApi.getCurrentUser();
    if (user) {
        usernameElement.textContent = user.username;
    }
    
    // Set up logout button
    logoutBtn.addEventListener('click', function() {
        authApi.logout();
    });
    
    // Load all student data
    loadDashboardData();
    
    async function loadDashboardData() {
        try {
            // Load dashboard summary
            await loadDashboardSummary();
            
            // Load courses
            await loadCourses();
            
            // Load predictions
            await loadPredictions();
            
        } catch (error) {
            console.error('Error loading dashboard data:', error);
        }
    }
    
    async function loadDashboardSummary() {
        try {
            const response = await apiClient.get('student/dashboard');
            console.log('Dashboard summary response:', response);
            
            if (response.status === 'success' && response.data) {
                const summary = response.data.summary;
                
                // Update summary cards
                if (gpaElement) gpaElement.textContent = summary.gpa;
                if (attendanceElement) attendanceElement.textContent = summary.attendance_rate + '%';
                if (assessmentsElement) assessmentsElement.textContent = summary.upcoming_assessments;
            }
        } catch (error) {
            console.error('Error loading dashboard summary:', error);
        }
    }
    
    async function loadCourses() {
        try {
            const response = await apiClient.get('student/courses');
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
    
    async function loadPredictions() {
        
        try {
            const response = await apiClient.get('student/predictions');
            console.log('Predictions response:', response);
            
            if (response.status === 'success' && response.data) {
                displayPredictions(response.data.predictions);
            } else {
                predictionsList.innerHTML = '<p class="text-gray-500">No predictions available</p>';
            }
        } catch (error) {
            console.error('Error loading predictions:', error);
            predictionsList.innerHTML = '<p class="text-red-500">Error loading predictions</p>';
        }
    }
    
    function displayCourses(courses) {
        if (!courses || courses.length === 0) {
            coursesList.innerHTML = '<p class="text-gray-500">No courses enrolled</p>';
            return;
        }
        
        let html = '';
        courses.forEach(course => {
            const statusColor = course.enrollment_status === 'completed' ? 'text-green-600' : 'text-blue-600';
            
            html += `
                <div class="border-b pb-3 mb-3 last:border-b-0">
                    <div class="flex justify-between items-start">
                        <div>
                            <h4 class="font-semibold">${course.course_name}</h4>
                            <p class="text-sm text-gray-600">${course.course_code} • ${course.credits} credits</p>
                        </div>
                        <span class="text-sm ${statusColor}">${course.enrollment_status}</span>
                    </div>
                    ${course.final_grade ? `<p class="text-sm mt-1">Final Grade: <span class="font-semibold">${course.final_grade}</span></p>` : ''}
                </div>
            `;
        });
        
        coursesList.innerHTML = html;
    }
    
    function displayPredictions(predictions) {
        if (!predictions || predictions.length === 0) {
            predictionsList.innerHTML = '<p class="text-gray-500">No predictions available</p>';
            return;
        }
        
        let html = '';
        predictions.forEach(prediction => {
            // Determine color based on predicted grade
            let gradeColor = 'text-green-600';
            if (prediction.predicted_grade === 'C' || prediction.predicted_grade === 'D') {
                gradeColor = 'text-yellow-600';
            } else if (prediction.predicted_grade === 'F') {
                gradeColor = 'text-red-600';
            }
            
            const confidencePercent = Math.round(prediction.confidence_score * 100);
            
            html += `
                <div class="border-b pb-3 mb-3 last:border-b-0">
                    <h4 class="font-semibold">${prediction.course_name}</h4>
                    <p class="text-sm text-gray-600">${prediction.course_code}</p>
                    <div class="mt-2 flex justify-between items-center">
                        <span>Predicted Grade: <span class="font-bold ${gradeColor}">${prediction.predicted_grade}</span></span>
                        <span class="text-sm text-gray-600">Confidence: ${confidencePercent}%</span>
                    </div>
                    <div class="mt-1 w-full bg-gray-200 rounded-full h-2">
                        <div class="bg-blue-600 h-2 rounded-full" style="width: ${confidencePercent}%"></div>
                    </div>
                </div>
            `;
        });
        
        predictionsList.innerHTML = html;
    }
});