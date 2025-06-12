document.addEventListener('DOMContentLoaded', function() {
    // Elements
    const usernameElement = document.getElementById('username');
    const logoutBtn = document.getElementById('logoutBtn');
    const loadingIndicator = document.getElementById('loadingIndicator');
    const mainContent = document.getElementById('mainContent');
    const assessmentTitle = document.getElementById('assessmentTitle');
    const assessmentDetails = document.getElementById('assessmentDetails');
    const maxScore = document.getElementById('maxScore');
    const totalStudents = document.getElementById('totalStudents');
    const gradedCount = document.getElementById('gradedCount');
    const pendingCount = document.getElementById('pendingCount');
    const averageScore = document.getElementById('averageScore');
    const gradeTableBody = document.getElementById('gradeTableBody');
    const saveAllBtn = document.getElementById('saveAllBtn');
    const exportBtn = document.getElementById('exportBtn');
    const statisticsBtn = document.getElementById('statisticsBtn');
    
    // Modals
    const statisticsModal = document.getElementById('statisticsModal');
    const successModal = document.getElementById('successModal');
    const closeStatsModal = document.getElementById('closeStatsModal');
    const closeModalBtn = document.getElementById('closeModalBtn');
    const modalTitle = document.getElementById('modalTitle');
    const modalMessage = document.getElementById('modalMessage');
    const statisticsContent = document.getElementById('statisticsContent');
    
    // State
    let currentAssessmentId = null;
    let assessmentData = null;
    let rosterData = [];
    let unsavedChanges = new Set();
    
    // Initialize
    init();
    
    function init() {
        // Check authentication
        if (!authApi.isLoggedIn()) {
            window.location.href = '../login.html';
            return;
        }
        
        // Display username
        const user = authApi.getCurrentUser();
        if (user) {
            usernameElement.textContent = user.username;
        }
        
        // Get assessment ID from URL
        const urlParams = new URLSearchParams(window.location.search);
        currentAssessmentId = urlParams.get('assessment_id');
        
        if (!currentAssessmentId) {
            showError('No assessment specified');
            return;
        }
        
        // Load assessment data
        loadAssessmentRoster();
        
        // Set up event listeners
        setupEventListeners();
    }
    
    function setupEventListeners() {
        // Logout
        logoutBtn.addEventListener('click', function() {
            authApi.logout();
        });
        
        // Save all grades
        saveAllBtn.addEventListener('click', function() {
            saveAllGrades();
        });
        
        // Export to CSV
        exportBtn.addEventListener('click', function() {
            exportToCSV();
        });
        
        // Show statistics
        statisticsBtn.addEventListener('click', function() {
            showStatistics();
        });
        
        // Modal close buttons
        closeStatsModal.addEventListener('click', function() {
            statisticsModal.classList.add('hidden');
        });
        
        closeModalBtn.addEventListener('click', function() {
            successModal.classList.add('hidden');
        });
        
        // Auto-save on window unload
        window.addEventListener('beforeunload', function(e) {
            if (unsavedChanges.size > 0) {
                e.preventDefault();
                e.returnValue = '';
                return 'You have unsaved changes. Are you sure you want to leave?';
            }
        });
    }
    
    async function loadAssessmentRoster() {
        try {
            console.log('Loading assessment roster for ID:', currentAssessmentId);
            const response = await apiClient.get(`faculty/assessments/${currentAssessmentId}/roster`);
            console.log('Roster response:', response);
            
            if (response.status === 'success' && response.data) {
                assessmentData = response.data.assessment;
                rosterData = response.data.roster;
                
                displayAssessmentInfo();
                displayRoster();
                updateStats();
            } else {
                showError('Failed to load assessment data');
            }
        } catch (error) {
            console.error('Error loading assessment roster:', error);
            if (error.response && error.response.status === 404) {
                showError('Assessment not found');
            } else if (error.response && error.response.status === 401) {
                showError('Session expired. Please log in again.');
                setTimeout(() => {
                    window.location.href = '../login.html';
                }, 2000);
            } else {
                showError('Failed to load assessment data. Please try again.');
            }
        } finally {
            loadingIndicator.classList.add('hidden');
            mainContent.classList.remove('hidden');
        }
    }
    
    function displayAssessmentInfo() {
        if (!assessmentData) return;
        
        assessmentTitle.textContent = assessmentData.title;
        maxScore.textContent = assessmentData.max_score;
        
        // Format details
        let details = '';
        if (assessmentData.due_date) {
            const dueDate = new Date(assessmentData.due_date);
            details += `Due: ${dueDate.toLocaleDateString()} ${dueDate.toLocaleTimeString()}`;
        }
        assessmentDetails.textContent = details;
    }
    
    function displayRoster() {
        if (!rosterData.length) {
            gradeTableBody.innerHTML = '<tr><td colspan="6" class="px-6 py-4 text-center text-gray-500">No students enrolled</td></tr>';
            return;
        }
        
        gradeTableBody.innerHTML = '';
        
        rosterData.forEach((student, index) => {
            const row = createStudentRow(student, index);
            gradeTableBody.appendChild(row);
        });
    }
    
    function createStudentRow(student, index) {
        const row = document.createElement('tr');
        row.className = 'hover:bg-gray-50';
        row.dataset.enrollmentId = student.enrollment_id;
        
        // Calculate grade letter
        const gradeLetter = calculateGradeLetter(student.percentage);
        
        row.innerHTML = `
            <td class="px-6 py-4 whitespace-nowrap">
                <div class="flex items-center">
                    <div class="w-10 h-10 bg-gray-300 rounded-full flex items-center justify-center text-gray-600 font-medium text-sm">
                        ${student.first_name[0]}${student.last_name[0]}
                    </div>
                    <div class="ml-4">
                        <div class="text-sm font-medium text-gray-900">${student.name}</div>
                        <div class="text-sm text-gray-500">ID: ${student.student_id}</div>
                    </div>
                </div>
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
                <input type="number" 
                       class="score-input w-20 px-2 py-1 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500" 
                       data-enrollment-id="${student.enrollment_id}"
                       data-original-score="${student.score || ''}"
                       value="${student.score || ''}" 
                       min="0" 
                       max="${assessmentData.max_score}" 
                       step="0.5"
                       placeholder="0">
                <span class="text-sm text-gray-500 ml-1">/ ${assessmentData.max_score}</span>
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
                <span class="percentage-display text-sm font-medium">
                    ${student.percentage ? student.percentage.toFixed(1) + '%' : '-'}
                </span>
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
                <span class="grade-letter inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getGradeColor(gradeLetter)}">
                    ${gradeLetter}
                </span>
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
                <span class="status-indicator inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(student.status)}">
                    ${getStatusText(student.status)}
                </span>
            </td>
            <td class="px-6 py-4">
                <input type="text" 
                       class="feedback-input w-full px-2 py-1 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 text-sm" 
                       data-enrollment-id="${student.enrollment_id}"
                       value="${student.feedback || ''}" 
                       placeholder="Optional feedback">
            </td>
        `;
        
        // Add event listeners to inputs
        const scoreInput = row.querySelector('.score-input');
        const feedbackInput = row.querySelector('.feedback-input');
        
        scoreInput.addEventListener('input', function() {
            handleScoreChange(this, student, row);
        });
        
        scoreInput.addEventListener('blur', function() {
            autoSaveGrade(student.enrollment_id);
        });
        
        feedbackInput.addEventListener('input', function() {
            handleFeedbackChange(this, student);
        });
        
        feedbackInput.addEventListener('blur', function() {
            autoSaveGrade(student.enrollment_id);
        });
        
        return row;
    }
    
    function handleScoreChange(input, student, row) {
        const score = parseFloat(input.value);
        const maxScoreValue = parseFloat(assessmentData.max_score);
        
        // Validate score
        if (isNaN(score) || score < 0 || score > maxScoreValue) {
            if (score > maxScoreValue) {
                input.value = maxScoreValue;
                score = maxScoreValue;
            }
        }
        
        // Update student data
        student.score = isNaN(score) ? null : score;
        student.percentage = student.score ? (student.score / maxScoreValue) * 100 : null;
        
        // Update UI
        const percentageDisplay = row.querySelector('.percentage-display');
        const gradeLetter = row.querySelector('.grade-letter');
        const statusIndicator = row.querySelector('.status-indicator');
        
        if (student.percentage !== null) {
            percentageDisplay.textContent = student.percentage.toFixed(1) + '%';
            const letter = calculateGradeLetter(student.percentage);
            gradeLetter.textContent = letter;
            gradeLetter.className = `inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getGradeColor(letter)}`;
            
            student.status = 'graded';
            statusIndicator.textContent = 'Graded';
            statusIndicator.className = `status-indicator inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor('graded')}`;
        } else {
            percentageDisplay.textContent = '-';
            gradeLetter.textContent = '-';
            gradeLetter.className = 'inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-gray-100 text-gray-800';
            
            student.status = student.submission_id ? 'submitted' : 'not_submitted';
            statusIndicator.textContent = getStatusText(student.status);
            statusIndicator.className = `status-indicator inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(student.status)}`;
        }
        
        // Mark as changed
        const originalScore = input.dataset.originalScore;
        if (input.value !== originalScore) {
            unsavedChanges.add(student.enrollment_id);
            input.classList.add('border-yellow-400', 'bg-yellow-50');
        } else {
            unsavedChanges.delete(student.enrollment_id);
            input.classList.remove('border-yellow-400', 'bg-yellow-50');
        }
        
        updateStats();
    }
    
    function handleFeedbackChange(input, student) {
        student.feedback = input.value.trim() || null;
        
        // Mark as changed if different from original
        const originalFeedback = student.feedback || '';
        if (input.value !== originalFeedback) {
            unsavedChanges.add(student.enrollment_id);
            input.classList.add('border-yellow-400', 'bg-yellow-50');
        } else {
            unsavedChanges.delete(student.enrollment_id);
            input.classList.remove('border-yellow-400', 'bg-yellow-50');
        }
    }
    
    async function autoSaveGrade(enrollmentId) {
        const student = rosterData.find(s => s.enrollment_id === enrollmentId);
        if (!student || !unsavedChanges.has(enrollmentId) || student.score === null) {
            return;
        }
        
        try {
            const response = await apiClient.post('faculty/assessments/grade', {
                enrollment_id: enrollmentId,
                assessment_id: currentAssessmentId,
                score: student.score,
                feedback: student.feedback
            });
            
            if (response.status === 'success') {
                // Mark as saved
                unsavedChanges.delete(enrollmentId);
                const inputs = document.querySelectorAll(`[data-enrollment-id="${enrollmentId}"]`);
                inputs.forEach(input => {
                    input.classList.remove('border-yellow-400', 'bg-yellow-50');
                    if (input.classList.contains('score-input')) {
                        input.dataset.originalScore = student.score;
                    }
                });
                
                // Show brief success indicator
                showBriefSuccess();
            }
        } catch (error) {
            console.error('Error auto-saving grade:', error);
        }
    }
    
    async function saveAllGrades() {
        const unsavedStudents = rosterData.filter(s => unsavedChanges.has(s.enrollment_id) && s.score !== null);
        
        if (unsavedStudents.length === 0) {
            showMessage('No changes to save', 'info');
            return;
        }
        
        // Disable save button
        saveAllBtn.disabled = true;
        saveAllBtn.textContent = 'Saving...';
        
        try {
            const grades = unsavedStudents.map(student => ({
                enrollment_id: student.enrollment_id,
                assessment_id: currentAssessmentId,
                score: student.score,
                feedback: student.feedback
            }));
            
            const response = await apiClient.post('faculty/assessments/bulk-grade', {
                grades: grades
            });
            
            if (response.status === 'success') {
                // Clear unsaved changes
                unsavedChanges.clear();
                
                // Update UI
                document.querySelectorAll('.score-input, .feedback-input').forEach(input => {
                    input.classList.remove('border-yellow-400', 'bg-yellow-50');
                    if (input.classList.contains('score-input')) {
                        input.dataset.originalScore = input.value;
                    }
                });
                
                showMessage(`Successfully saved ${response.data.summary.successful} grades!`, 'success');
                updateStats();
            } else {
                showMessage('Failed to save some grades', 'error');
            }
        } catch (error) {
            console.error('Error saving grades:', error);
            showMessage('Failed to save grades. Please try again.', 'error');
        } finally {
            saveAllBtn.disabled = false;
            saveAllBtn.textContent = 'Save All Grades';
        }
    }
    
    function updateStats() {
        const total = rosterData.length;
        const graded = rosterData.filter(s => s.score !== null).length;
        const pending = total - graded;
        
        totalStudents.textContent = total;
        gradedCount.textContent = graded;
        pendingCount.textContent = pending;
        
        // Calculate average
        const gradedStudents = rosterData.filter(s => s.score !== null);
        if (gradedStudents.length > 0) {
            const avg = gradedStudents.reduce((sum, s) => sum + s.score, 0) / gradedStudents.length;
            averageScore.textContent = avg.toFixed(1);
        } else {
            averageScore.textContent = '-';
        }
    }
    
    function calculateGradeLetter(percentage) {
        if (percentage === null || percentage === undefined) return '-';
        if (percentage >= 90) return 'A';
        if (percentage >= 80) return 'B';
        if (percentage >= 70) return 'C';
        if (percentage >= 60) return 'D';
        return 'F';
    }
    
    function getGradeColor(grade) {
        switch (grade) {
            case 'A': return 'bg-green-100 text-green-800';
            case 'B': return 'bg-blue-100 text-blue-800';
            case 'C': return 'bg-yellow-100 text-yellow-800';
            case 'D': return 'bg-orange-100 text-orange-800';
            case 'F': return 'bg-red-100 text-red-800';
            default: return 'bg-gray-100 text-gray-800';
        }
    }
    
    function getStatusColor(status) {
        switch (status) {
            case 'graded': return 'bg-green-100 text-green-800';
            case 'submitted': return 'bg-blue-100 text-blue-800';
            case 'not_submitted': return 'bg-gray-100 text-gray-800';
            default: return 'bg-gray-100 text-gray-800';
        }
    }
    
    function getStatusText(status) {
        switch (status) {
            case 'graded': return 'Graded';
            case 'submitted': return 'Submitted';
            case 'not_submitted': return 'Not Submitted';
            default: return 'Unknown';
        }
    }
    
    async function showStatistics() {
        try {
            const response = await apiClient.get(`faculty/assessments/${currentAssessmentId}/statistics`);
            
            if (response.status === 'success' && response.data.statistics) {
                displayStatistics(response.data);
                statisticsModal.classList.remove('hidden');
            } else {
                showMessage('No statistics available yet', 'info');
            }
        } catch (error) {
            console.error('Error loading statistics:', error);
            showMessage('Failed to load statistics', 'error');
        }
    }
    
    function displayStatistics(data) {
        const stats = data.statistics;
        
        statisticsContent.innerHTML = `
            <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                <div class="text-center p-4 bg-gray-50 rounded-lg">
                    <div class="text-2xl font-bold text-gray-700">${stats.total_submissions}</div>
                    <div class="text-sm text-gray-500">Submissions</div>
                </div>
                <div class="text-center p-4 bg-blue-50 rounded-lg">
                    <div class="text-2xl font-bold text-blue-600">${stats.average_score}</div>
                    <div class="text-sm text-gray-500">Average Score</div>
                </div>
                <div class="text-center p-4 bg-green-50 rounded-lg">
                    <div class="text-2xl font-bold text-green-600">${stats.highest_score}</div>
                    <div class="text-sm text-gray-500">Highest Score</div>
                </div>
                <div class="text-center p-4 bg-red-50 rounded-lg">
                    <div class="text-2xl font-bold text-red-600">${stats.lowest_score}</div>
                    <div class="text-sm text-gray-500">Lowest Score</div>
                </div>
            </div>
            
            <h4 class="font-semibold mb-2">Grade Distribution</h4>
            <div class="space-y-2">
                ${Object.entries(stats.grade_distribution).map(([grade, count]) => `
                    <div class="flex justify-between items-center">
                        <span class="font-medium">${grade} Grade:</span>
                        <div class="flex items-center">
                            <div class="w-32 bg-gray-200 rounded-full h-2 mr-2">
                                <div class="h-2 rounded-full ${getGradeColor(grade).split(' ')[0]}" 
                                     style="width: ${(count / stats.total_submissions * 100)}%"></div>
                            </div>
                            <span class="text-sm text-gray-600">${count} students</span>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    }
    
    function exportToCSV() {
        let csv = 'Student ID,Name,Score,Percentage,Grade,Status,Feedback\n';
        
        rosterData.forEach(student => {
            const grade = calculateGradeLetter(student.percentage);
            const status = getStatusText(student.status);
            csv += `"${student.student_id}","${student.name}","${student.score || ''}","${student.percentage ? student.percentage.toFixed(1) : ''}","${grade}","${status}","${student.feedback || ''}"\n`;
        });
        
        // Download CSV
        const blob = new Blob([csv], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${assessmentData.title.replace(/[^a-z0-9]/gi, '_')}_grades.csv`;
        a.click();
        window.URL.revokeObjectURL(url);
    }
    
    function showMessage(message, type) {
        modalTitle.textContent = type === 'success' ? 'Success!' : type === 'error' ? 'Error' : 'Information';
        modalMessage.textContent = message;
        successModal.classList.remove('hidden');
    }
    
    function showBriefSuccess() {
        // Show a brief success indicator
        const indicator = document.createElement('div');
        indicator.className = 'fixed top-4 right-4 bg-green-500 text-white px-4 py-2 rounded-md shadow-lg z-50';
        indicator.textContent = 'Auto-saved';
        document.body.appendChild(indicator);
        
        setTimeout(() => {
            indicator.remove();
        }, 2000);
    }
    
    function showError(message) {
        console.error(message);
        alert(message); // Simple error display for now
    }
});