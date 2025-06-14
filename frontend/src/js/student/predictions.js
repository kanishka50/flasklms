document.addEventListener('DOMContentLoaded', function() {
    // Elements
    const usernameElement = document.getElementById('username');
    const logoutBtn = document.getElementById('logoutBtn');
    const courseFilter = document.getElementById('courseFilter');
    const riskFilter = document.getElementById('riskFilter');
    const searchInput = document.getElementById('searchInput');
    const applyFiltersBtn = document.getElementById('applyFilters');
    const clearFiltersBtn = document.getElementById('clearFilters');
    const generateAllBtn = document.getElementById('generateAll');
    const exportBtn = document.getElementById('exportBtn');
    const loadingIndicator = document.getElementById('loadingIndicator');
    const predictionsContainer = document.getElementById('predictionsContainer');
    const noPredictions = document.getElementById('noPredictions');
    const predictionsGrid = document.getElementById('predictionsGrid');
    const predictionCount = document.getElementById('predictionCount');
    
    // Summary elements
    const totalCourses = document.getElementById('totalCourses');
    const lowRiskCount = document.getElementById('lowRiskCount');
    const mediumRiskCount = document.getElementById('mediumRiskCount');
    const highRiskCount = document.getElementById('highRiskCount');
    
    // State
    let allPredictions = [];
    let filteredPredictions = [];
    
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
        if (user && usernameElement) {
            usernameElement.textContent = user.username;
        }
        
        // Load predictions
        loadPredictions();
        
        // Set up event listeners
        setupEventListeners();
    }
    
    function setupEventListeners() {
        // Logout
        if (logoutBtn) {
            logoutBtn.addEventListener('click', function() {
                authApi.logout();
            });
        }
        
        // Filter controls
        if (applyFiltersBtn) {
            applyFiltersBtn.addEventListener('click', applyFilters);
        }
        
        if (clearFiltersBtn) {
            clearFiltersBtn.addEventListener('click', clearFilters);
        }
        
        // Generate predictions button
        if (generateAllBtn) {
            generateAllBtn.addEventListener('click', generatePredictions);
        }
        
        // Export functionality
        if (exportBtn) {
            exportBtn.addEventListener('click', exportPredictions);
        }
        
        // Search on enter
        if (searchInput) {
            searchInput.addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    applyFilters();
                }
            });
        }
    }
    
    async function loadPredictions() {
        try {
            showLoading(true);
            
            const response = await apiClient.get('student/predictions');
            console.log('Predictions response:', response);
            
            if (response.status === 'success' && response.data) {
                // Extract predictions from the response structure
                allPredictions = [];
                
                if (response.data.predictions && Array.isArray(response.data.predictions)) {
                    response.data.predictions.forEach(item => {
                        if (item.prediction) {
                            // Add course info to prediction
                            const prediction = {
                                ...item.prediction,
                                course_code: item.course.course_code,
                                course_name: item.course.course_name,
                                enrollment_id: item.enrollment_id
                            };
                            allPredictions.push(prediction);
                        }
                    });
                }
                
                filteredPredictions = [...allPredictions];
                
                // Populate course filter
                populateCourseFilter();
                
                // Update summary
                updateSummary();
                
                // Display predictions
                displayPredictions();
            } else {
                showNoPredictions();
            }
        } catch (error) {
            console.error('Error loading predictions:', error);
            showError('Failed to load predictions. Please try again.');
        } finally {
            showLoading(false);
        }
    }
    
    function populateCourseFilter() {
        if (!courseFilter) return;
        
        courseFilter.innerHTML = '<option value="">All Courses</option>';
        
        // Get unique courses
        const courses = new Map();
        allPredictions.forEach(pred => {
            if (!courses.has(pred.course_code)) {
                courses.set(pred.course_code, pred.course_name);
            }
        });
        
        // Add to filter
        courses.forEach((name, code) => {
            const option = document.createElement('option');
            option.value = code;
            option.textContent = `${code} - ${name}`;
            courseFilter.appendChild(option);
        });
    }
    
    function updateSummary() {
        // Count by risk level
        const riskCounts = {
            low: 0,
            medium: 0,
            high: 0
        };
        
        filteredPredictions.forEach(pred => {
            if (riskCounts.hasOwnProperty(pred.risk_level)) {
                riskCounts[pred.risk_level]++;
            }
        });
        
        // Update UI
        if (totalCourses) totalCourses.textContent = filteredPredictions.length;
        if (lowRiskCount) lowRiskCount.textContent = riskCounts.low;
        if (mediumRiskCount) mediumRiskCount.textContent = riskCounts.medium;
        if (highRiskCount) highRiskCount.textContent = riskCounts.high;
        if (predictionCount) predictionCount.textContent = filteredPredictions.length;
    }
    
    function displayPredictions() {
        if (filteredPredictions.length === 0) {
            showNoPredictions();
            return;
        }
        
        predictionsContainer.classList.remove('hidden');
        noPredictions.classList.add('hidden');
        
        let html = '';
        filteredPredictions.forEach(prediction => {
            html += createPredictionCard(prediction);
        });
        
        predictionsGrid.innerHTML = html;
        
        // Add click handlers for detail view
        document.querySelectorAll('.view-details-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                const predictionId = this.dataset.predictionId;
                const prediction = allPredictions.find(p => p.prediction_id == predictionId);
                if (prediction) {
                    showPredictionDetail(prediction);
                }
            });
        });
    }
    
    function createPredictionCard(prediction) {
        const riskColors = {
            'low': 'bg-green-100 text-green-800 border-green-200',
            'medium': 'bg-yellow-100 text-yellow-800 border-yellow-200',
            'high': 'bg-red-100 text-red-800 border-red-200'
        };
        
        const gradeColors = {
            'Pass': 'text-green-600',
            'Fail': 'text-red-600',
            'A': 'text-green-600',
            'B': 'text-blue-600',
            'C': 'text-yellow-600',
            'D': 'text-orange-600',
            'F': 'text-red-600'
        };
        
        const riskBorderColors = {
            'low': 'border-l-green-500',
            'medium': 'border-l-yellow-500',
            'high': 'border-l-red-500'
        };
        
        const confidencePercent = Math.round(prediction.confidence_score * 100);
        const riskClass = riskColors[prediction.risk_level] || riskColors['medium'];
        const gradeColor = gradeColors[prediction.predicted_grade] || 'text-gray-600';
        const borderColor = riskBorderColors[prediction.risk_level] || 'border-l-gray-500';
        
        return `
            <div class="prediction-card bg-white rounded-lg shadow-md hover:shadow-lg border-l-4 ${borderColor}">
                <div class="p-6">
                    <div class="mb-4">
                        <h3 class="text-lg font-semibold text-gray-900">${prediction.course_name}</h3>
                        <p class="text-sm text-gray-600">${prediction.course_code}</p>
                    </div>
                    
                    <div class="space-y-4">
                        <div class="flex justify-between items-center">
                            <span class="text-sm text-gray-500">Predicted Grade</span>
                            <span class="text-2xl font-bold ${gradeColor}">${prediction.predicted_grade}</span>
                        </div>
                        
                        <div>
                            <div class="flex justify-between items-center mb-1">
                                <span class="text-sm text-gray-500">Confidence</span>
                                <span class="text-sm font-medium">${confidencePercent}%</span>
                            </div>
                            <div class="w-full bg-gray-200 rounded-full h-2">
                                <div class="bg-blue-600 h-2 rounded-full transition-all duration-300" 
                                     style="width: ${confidencePercent}%"></div>
                            </div>
                        </div>
                        
                        <div class="flex justify-between items-center">
                            <span class="text-sm text-gray-500">Risk Level</span>
                            <span class="px-3 py-1 rounded-full text-xs font-medium border ${riskClass}">
                                ${prediction.risk_level.toUpperCase()}
                            </span>
                        </div>
                        
                        <div class="text-xs text-gray-400 border-t pt-3">
                            <i class="fas fa-clock mr-1"></i>
                            Updated: ${new Date(prediction.prediction_date).toLocaleDateString()}
                        </div>
                        
                        <button class="view-details-btn w-full mt-3 bg-blue-600 hover:bg-blue-700 text-white text-sm py-2 px-4 rounded transition-colors"
                                data-prediction-id="${prediction.prediction_id}">
                            <i class="fas fa-info-circle mr-1"></i> View Details
                        </button>
                    </div>
                </div>
            </div>
        `;
    }
    
    function showPredictionDetail(prediction) {
        // Get explanation if available
        let explanationHtml = '';
        if (prediction.explanation) {
            explanationHtml = `
                <div class="mt-6 border-t pt-4">
                    <h4 class="font-semibold mb-2">Analysis:</h4>
                    <p class="text-gray-600">${prediction.explanation.explanation || 'Based on your current performance metrics.'}</p>
                    ${prediction.explanation.top_factors && prediction.explanation.top_factors.length > 0 ? `
                        <div class="mt-4">
                            <h5 class="font-medium mb-2">Key Factors:</h5>
                            <ul class="space-y-2">
                                ${prediction.explanation.top_factors.slice(0, 3).map(factor => `
                                    <li class="flex justify-between items-center bg-gray-50 p-2 rounded">
                                        <span class="text-sm">${factor.name.replace(/_/g, ' ')}</span>
                                        <span class="text-sm font-medium">${(factor.importance * 100).toFixed(1)}% impact</span>
                                    </li>
                                `).join('')}
                            </ul>
                        </div>
                    ` : ''}
                </div>
            `;
        }
        
        // Show modal with details
        const modalHtml = `
            <div class="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50 p-4" id="detailModal">
                <div class="bg-white rounded-lg p-6 max-w-2xl w-full max-h-[90vh] overflow-y-auto">
                    <div class="flex justify-between items-start mb-4">
                        <h3 class="text-xl font-bold text-gray-900">${prediction.course_name}</h3>
                        <button onclick="document.getElementById('detailModal').remove()" 
                                class="text-gray-400 hover:text-gray-600">
                            <i class="fas fa-times text-xl"></i>
                        </button>
                    </div>
                    
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                        <div class="bg-gray-50 p-4 rounded">
                            <div class="text-sm text-gray-500 mb-1">Course Code</div>
                            <div class="font-medium">${prediction.course_code}</div>
                        </div>
                        <div class="bg-gray-50 p-4 rounded">
                            <div class="text-sm text-gray-500 mb-1">Enrollment ID</div>
                            <div class="font-medium">#${prediction.enrollment_id}</div>
                        </div>
                    </div>
                    
                    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div class="text-center p-4 bg-blue-50 rounded">
                            <div class="text-3xl font-bold ${prediction.predicted_grade === 'Pass' ? 'text-green-600' : 'text-red-600'}">
                                ${prediction.predicted_grade}
                            </div>
                            <div class="text-sm text-gray-600 mt-1">Predicted Grade</div>
                        </div>
                        <div class="text-center p-4 bg-purple-50 rounded">
                            <div class="text-3xl font-bold text-purple-600">
                                ${Math.round(prediction.confidence_score * 100)}%
                            </div>
                            <div class="text-sm text-gray-600 mt-1">Confidence</div>
                        </div>
                        <div class="text-center p-4 bg-${prediction.risk_level === 'low' ? 'green' : prediction.risk_level === 'medium' ? 'yellow' : 'red'}-50 rounded">
                            <div class="text-3xl font-bold text-${prediction.risk_level === 'low' ? 'green' : prediction.risk_level === 'medium' ? 'yellow' : 'red'}-600">
                                ${prediction.risk_level.toUpperCase()}
                            </div>
                            <div class="text-sm text-gray-600 mt-1">Risk Level</div>
                        </div>
                    </div>
                    
                    <div class="mt-4 text-sm text-gray-500">
                        <i class="fas fa-calendar-alt mr-2"></i>
                        Last Updated: ${new Date(prediction.prediction_date).toLocaleString()}
                    </div>
                    
                    ${explanationHtml}
                    
                    <div class="mt-6 flex space-x-2">
                        <button onclick="document.getElementById('detailModal').remove()" 
                                class="flex-1 bg-gray-600 hover:bg-gray-700 text-white py-2 px-4 rounded transition-colors">
                            Close
                        </button>
                        <button onclick="generateSinglePrediction('${prediction.enrollment_id}')" 
                                class="flex-1 bg-blue-600 hover:bg-blue-700 text-white py-2 px-4 rounded transition-colors">
                            <i class="fas fa-sync-alt mr-1"></i> Refresh Prediction
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', modalHtml);
    }
    
    function applyFilters() {
        const courseCode = courseFilter ? courseFilter.value : '';
        const riskLevel = riskFilter ? riskFilter.value : '';
        const searchTerm = searchInput ? searchInput.value.toLowerCase() : '';
        
        filteredPredictions = allPredictions.filter(prediction => {
            const matchesCourse = !courseCode || prediction.course_code === courseCode;
            const matchesRisk = !riskLevel || prediction.risk_level === riskLevel;
            const matchesSearch = !searchTerm || 
                prediction.course_name.toLowerCase().includes(searchTerm) ||
                prediction.course_code.toLowerCase().includes(searchTerm);
            
            return matchesCourse && matchesRisk && matchesSearch;
        });
        
        updateSummary();
        displayPredictions();
    }
    
    function clearFilters() {
        if (courseFilter) courseFilter.value = '';
        if (riskFilter) riskFilter.value = '';
        if (searchInput) searchInput.value = '';
        filteredPredictions = [...allPredictions];
        updateSummary();
        displayPredictions();
    }
    
    async function generatePredictions() {
        if (!confirm('Generate new predictions for all your courses? This may take a moment.')) {
            return;
        }
        
        try {
            showLoading(true);
            
            // For each enrollment, generate a prediction
            const promises = allPredictions.map(pred => 
                apiClient.post(`prediction/student/${pred.enrollment_id}/generate`)
            );
            
            const results = await Promise.allSettled(promises);
            
            // Count successes
            const successful = results.filter(r => r.status === 'fulfilled').length;
            const failed = results.filter(r => r.status === 'rejected').length;
            
            // Reload predictions
            await loadPredictions();
            
            // Show result
            if (failed === 0) {
                alert(`All ${successful} predictions updated successfully!`);
            } else {
                alert(`Updated ${successful} predictions. ${failed} failed to update.`);
            }
        } catch (error) {
            console.error('Error generating predictions:', error);
            alert('Failed to generate predictions. Please try again.');
        } finally {
            showLoading(false);
        }
    }
    
    async function generateSinglePrediction(enrollmentId) {
        try {
            // Close modal first
            const modal = document.getElementById('detailModal');
            if (modal) modal.remove();
            
            showLoading(true);
            
            await apiClient.post(`prediction/student/${enrollmentId}/generate`);
            
            // Reload all predictions
            await loadPredictions();
            
            // Find and show the updated prediction
            const updatedPrediction = allPredictions.find(p => p.enrollment_id == enrollmentId);
            if (updatedPrediction) {
                showPredictionDetail(updatedPrediction);
            }
        } catch (error) {
            console.error('Error generating prediction:', error);
            alert('Failed to update prediction. Please try again.');
        } finally {
            showLoading(false);
        }
    }
    
    function exportPredictions() {
        if (filteredPredictions.length === 0) {
            alert('No predictions to export');
            return;
        }
        
        // Create CSV content
        const headers = ['Course Code', 'Course Name', 'Predicted Grade', 'Confidence (%)', 'Risk Level', 'Last Updated'];
        const rows = filteredPredictions.map(p => [
            p.course_code,
            p.course_name,
            p.predicted_grade,
            Math.round(p.confidence_score * 100),
            p.risk_level,
            new Date(p.prediction_date).toLocaleDateString()
        ]);
        
        let csvContent = headers.join(',') + '\n';
        rows.forEach(row => {
            csvContent += row.map(cell => `"${cell}"`).join(',') + '\n';
        });
        
        // Download file
        const blob = new Blob([csvContent], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `grade_predictions_${new Date().toISOString().split('T')[0]}.csv`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
    }
    
    function showLoading(show) {
        if (show) {
            loadingIndicator.classList.remove('hidden');
            predictionsContainer.classList.add('hidden');
            noPredictions.classList.add('hidden');
        } else {
            loadingIndicator.classList.add('hidden');
        }
    }
    
    function showNoPredictions() {
        predictionsContainer.classList.add('hidden');
        noPredictions.classList.remove('hidden');
        updateSummary();
    }
    
    function showError(message) {
        predictionsGrid.innerHTML = `
            <div class="col-span-full text-center py-8">
                <div class="text-red-500 text-6xl mb-4">
                    <i class="fas fa-exclamation-triangle"></i>
                </div>
                <p class="text-red-600 text-lg">${message}</p>
                <button onclick="location.reload()" class="mt-4 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded">
                    Try Again
                </button>
            </div>
        `;
        predictionsContainer.classList.remove('hidden');
        noPredictions.classList.add('hidden');
    }
});