document.addEventListener('DOMContentLoaded', function() {
    // Check authentication
    if (!authApi.isLoggedIn() || !authApi.hasRole('student')) {
        window.location.href = '../login.html';
        return;
    }
    
    // Get assessment ID from URL
    const urlParams = new URLSearchParams(window.location.search);
    const assessmentId = urlParams.get('assessment_id');
    
    if (!assessmentId) {
        alert('No assessment ID provided');
        window.location.href = 'assessments.html';
        return;
    }
    
    // DOM elements
    const loadingIndicator = document.getElementById('loadingIndicator');
    const mainContent = document.getElementById('mainContent');
    const assessmentTitle = document.getElementById('assessmentTitle');
    const courseName = document.getElementById('courseName');
    const assessmentType = document.getElementById('assessmentType');
    const dueDate = document.getElementById('dueDate');
    const maxScore = document.getElementById('maxScore');
    const weight = document.getElementById('weight');
    const status = document.getElementById('status');
    const description = document.getElementById('description');
    const descriptionSection = document.getElementById('descriptionSection');
    
    // Submission elements
    const submissionStatus = document.getElementById('submissionStatus');
    const submissionForm = document.getElementById('submissionForm');
    const assessmentSubmitForm = document.getElementById('assessmentSubmitForm');
    const submissionText = document.getElementById('submissionText');
    const submitBtn = document.getElementById('submitBtn');
    const cancelBtn = document.getElementById('cancelBtn');
    
    // Previous submission elements
    const previousSubmission = document.getElementById('previousSubmission');
    const previousSubmissionContent = document.getElementById('previousSubmissionContent');
    const feedbackSection = document.getElementById('feedbackSection');
    const feedback = document.getElementById('feedback');
    
    // Modal elements
    const successModal = document.getElementById('successModal');
    const closeModalBtn = document.getElementById('closeModalBtn');
    
    // State
    let assessmentData = null;
    let isSubmitted = false;
    
    // Initialize
    initialize();
    
    async function initialize() {
        try {
            await loadAssessmentDetails();
            setupEventListeners();
        } catch (error) {
            console.error('Initialization error:', error);
            showError('Failed to initialize page');
        }
    }
    
    async function loadAssessmentDetails() {
        try {
            showLoading(true);
            
            const response = await apiClient.get(`student/assessments/${assessmentId}`);
            
            if (response.status === 'success' && response.data) {
                assessmentData = response.data;
                displayAssessmentInfo();
                checkSubmissionStatus();
                showLoading(false);
            } else {
                throw new Error('Failed to load assessment details');
            }
        } catch (error) {
            console.error('Error loading assessment:', error);
            showError('Failed to load assessment. Redirecting...');
            setTimeout(() => {
                window.location.href = 'assessments.html';
            }, 2000);
        }
    }
    
    function displayAssessmentInfo() {
        assessmentTitle.textContent = assessmentData.title;
        courseName.textContent = `${assessmentData.course_code} - ${assessmentData.course_name}`;
        assessmentType.textContent = assessmentData.type_name;
        maxScore.textContent = `${assessmentData.max_score} points`;
        weight.textContent = assessmentData.weight ? `${assessmentData.weight}%` : 'Not specified';
        
        // Format due date
        if (assessmentData.due_date) {
            const date = new Date(assessmentData.due_date);
            dueDate.textContent = `${date.toLocaleDateString()} ${date.toLocaleTimeString()}`;
            
            // Check if overdue
            if (new Date() > date && assessmentData.status !== 'graded') {
                dueDate.classList.add('text-red-600', 'font-semibold');
                dueDate.innerHTML += ' <span class="text-xs">(Overdue)</span>';
            }
        } else {
            dueDate.textContent = 'No due date';
        }
        
        // Display description if exists
        if (assessmentData.description) {
            description.textContent = assessmentData.description;
            descriptionSection.classList.remove('hidden');
        }
        
        // Display status
        updateStatus();
    }
    
    function updateStatus() {
        status.textContent = assessmentData.status === 'graded' ? 'Graded' : 
                           assessmentData.submission_date ? 'Submitted' : 'Not Submitted';
        
        if (assessmentData.status === 'graded') {
            status.className = 'font-medium text-green-600';
        } else if (assessmentData.submission_date) {
            status.className = 'font-medium text-blue-600';
        } else {
            status.className = 'font-medium text-yellow-600';
        }
    }
    
    function checkSubmissionStatus() {
        isSubmitted = !!assessmentData.submission_date;
        
        if (isSubmitted) {
            // Show submission status
            submissionStatus.classList.remove('hidden');
            document.getElementById('submissionDate').textContent = 
                new Date(assessmentData.submission_date).toLocaleString();
            
            // Show grade if available
            if (assessmentData.score !== null) {
                document.getElementById('gradeInfo').classList.remove('hidden');
                document.getElementById('grade').textContent = 
                    `${assessmentData.score}/${assessmentData.max_score} (${assessmentData.percentage.toFixed(1)}%)`;
            }
            
            // Show previous submission
            if (assessmentData.submission_text) {
                previousSubmission.classList.remove('hidden');
                previousSubmissionContent.innerHTML = `
                    <div class="bg-gray-50 p-4 rounded-md">
                        <pre class="whitespace-pre-wrap text-sm">${assessmentData.submission_text}</pre>
                    </div>
                `;
            }
            
            // Show feedback if available
            if (assessmentData.feedback) {
                feedbackSection.classList.remove('hidden');
                feedback.textContent = assessmentData.feedback;
            }
            
            // Disable form if already graded
            if (assessmentData.status === 'graded') {
                submissionForm.classList.add('opacity-50');
                submissionText.disabled = true;
                submitBtn.disabled = true;
                submitBtn.textContent = 'Already Graded';
            } else {
                // Allow resubmission if not graded
                submitBtn.textContent = 'Resubmit Assessment';
            }
        }
    }
    
    function setupEventListeners() {
        // Form submission
        assessmentSubmitForm.addEventListener('submit', function(e) {
            e.preventDefault();
            submitAssessment();
        });
        
        // Cancel button
        cancelBtn.addEventListener('click', function() {
            if (submissionText.value.trim() && !confirm('You have unsaved changes. Are you sure you want to cancel?')) {
                return;
            }
            window.location.href = 'assessments.html';
        });
        
        // Modal close
        closeModalBtn.addEventListener('click', function() {
            window.location.href = 'assessments.html';
        });
    }
    
    async function submitAssessment() {
        const text = submissionText.value.trim();
        
        if (!text) {
            alert('Please enter your submission text');
            return;
        }
        
        // Confirm submission
        const confirmMsg = isSubmitted ? 
            'Are you sure you want to resubmit? This will replace your previous submission.' :
            'Are you sure you want to submit? You may not be able to change it after grading.';
            
        if (!confirm(confirmMsg)) {
            return;
        }
        
        try {
            // Disable submit button
            submitBtn.disabled = true;
            submitBtn.textContent = 'Submitting...';
            
            const response = await apiClient.post(`student/assessments/${assessmentId}/submit`, {
                submission_text: text,
                file_url: null // Placeholder for future file upload
            });
            
            if (response.status === 'success') {
                // Show success modal
                successModal.classList.remove('hidden');
            } else {
                showError(response.message || 'Failed to submit assessment');
            }
            
        } catch (error) {
            console.error('Error submitting assessment:', error);
            
            if (error.response && error.response.status === 401) {
                showError('Session expired. Please log in again.');
                setTimeout(() => {
                    authApi.logout();
                }, 2000);
            } else {
                showError('Failed to submit assessment. Please try again.');
            }
        } finally {
            // Re-enable submit button
            submitBtn.disabled = false;
            submitBtn.textContent = isSubmitted ? 'Resubmit Assessment' : 'Submit Assessment';
        }
    }
    
    function showLoading(show) {
        if (show) {
            loadingIndicator.classList.remove('hidden');
            mainContent.classList.add('hidden');
        } else {
            loadingIndicator.classList.add('hidden');
            mainContent.classList.remove('hidden');
        }
    }
    
    function showError(message) {
        console.error(message);
        alert(message);
    }
});