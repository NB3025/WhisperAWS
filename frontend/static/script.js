$(document).ready(function() {
    updateTable();
    setInterval(updateTable, 5000); // 5초마다 테이블 업데이트
});

function uploadFiles() {
    var formData = new FormData($('#uploadForm')[0]);
    var fileInput = $('#fileInput');
    var uploadButton = $('#uploadButton');
    var progressBar = $('#progressBar');
    var progressBarContainer = $('#progressBarContainer');
    var uploadStatus = $('#uploadStatus');

    if (fileInput[0].files.length === 0) {
        uploadStatus.text('Please select files to upload.');
        return;
    }

    uploadButton.prop('disabled', true);
    fileInput.prop('disabled', true);
    progressBarContainer.show();
    uploadStatus.text('Uploading...');

    $.ajax({
        url: '/',
        type: 'POST',
        data: formData,
        processData: false,
        contentType: false,
        xhr: function() {
            var xhr = new window.XMLHttpRequest();
            xhr.upload.addEventListener("progress", function(evt) {
                if (evt.lengthComputable) {
                    var percentComplete = evt.loaded / evt.total;
                    progressBar.width(percentComplete * 100 + '%');
                }
            }, false);
            return xhr;
        },
        success: function(response) {
            uploadStatus.text('Files uploaded successfully!');
            updateTable();
        },
        error: function(xhr, status, error) {
            uploadStatus.text('Error uploading files: ' + error);
        },
        complete: function() {
            uploadButton.prop('disabled', false);
            fileInput.prop('disabled', false);
            progressBarContainer.hide();
            progressBar.width('0%');
        }
    });
}

// 날짜 형식을 변환하는 함수 추가
function formatDate(dateString) {
    if (!dateString) return 'N/A';
    
    const date = new Date(dateString);
    
    // 날짜가 유효하지 않으면 원래 문자열 반환
    if (isNaN(date.getTime())) return dateString;
    
    const year = date.getUTCFullYear();
    const month = String(date.getUTCMonth() + 1).padStart(2, '0');
    const day = String(date.getUTCDate()).padStart(2, '0');
    const hours = String(date.getUTCHours()).padStart(2, '0');
    const minutes = String(date.getUTCMinutes()).padStart(2, '0');
    const seconds = String(date.getUTCSeconds()).padStart(2, '0');
    
    return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
}

function updateTable() {
    $.ajax({
        url: '/get_items',
        type: 'GET',
        success: function(data) {
            var tableBody = $('#statusTableBody');
            tableBody.empty();
            
            data.forEach(function(item) {
                var row = $('<tr>');

                // Job ID의 앞 6자리만 표시
                var shortJobId = item.JobId.substring(0, 6);
                row.append($('<td>').text(shortJobId));

                row.append($('<td>').text(item.CreatedAt));

                // Created At 형식 변환
                // row.append($('<td>').text(formatDate(item.CreatedAt)));
                
                // Completed At 형식 변환
                // row.append($('<td>').text(formatDate(item.CompletedAt)));
                row.append($('<td>').text(item.CompletedAt || 'N/A'));
                

                var statusCell = $('<td>').text(item.Status);
                if (item.Status === 'STARTED') {
                    statusCell.css('color', 'green');
                } else if (item.Status === 'COMPLETED') {
                    statusCell.css('color', 'blue');
                }
                row.append(statusCell);
                
                // Decode the S3 address to show the original Korean filename
                var decodedS3Address = decodeURIComponent(item.S3Address);
                row.append($('<td>').text(decodedS3Address));

                row.append($('<td>').text(item.Output));
                tableBody.append(row);
            });
        },
        error: function(xhr, status, error) {
            console.error('Error fetching data:', error);
        }
    });
}