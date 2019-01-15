function timeout(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

async function collectDatasetIds() {
    let datasetIds = [];
    $(".dataset-id").each(function() {
        let dsid = $(this).val();
        datasetIds.push(dsid);
    });
    return datasetIds;
}

async function checkDatasetRunning(datasetId) {
    let result = await $.getJSON(`/checkerrunning?dsid=${datasetId}`);
    // console.log(JSON.stringify(result));
    if ( result.running === true ) {
        return datasetId;
    } else {
        return null;
    }
}

async function getRunningDatasets(datasetIds) {
    var runningDatasets = [];
    for (var idx of datasetIds) {
        const result = await checkDatasetRunning(idx);
        if (result != null) {
            runningDatasets.push(idx);
        }
    }
    return runningDatasets;
}

function initRunningProgress(datasetId) {
    // Disable button
    $(`#dataset-checker-button-${datasetId}`).attr("disabled", "disabled").html('Checker Running');
    // Setup progress data
    let infoRow = $(`#dataset-${datasetId}-info-row`);
    let newRow = $(`<div class="row">
                        <div class="row col-lg-12" id="dataset-${datasetId}-status-row">
                            <div class="progress-bar col-lg-12" id="dataset-${datasetId}-progress-bar">
                                <div class="progress-label" id="dataset-${datasetId}-progress">
                                    0 %
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="row" style="border: none;">
                        <div class="col-lg-12 text-center" id="dataset-${datasetId}-status">
                            ...
                        </div>
                    </div><br>`);
    newRow.progressbar();
    newRow.insertAfter(infoRow);
}

async function launchMonitoring(datasetId) {
    const statusUrl = '/checkerstatus?dsid='+datasetId;
    var result = await $.getJSON(statusUrl);
    var progress = result.progress + 10;
    
    // Monitor status
    updateProgress(progress, statusUrl, datasetId);
    // updateProgress(statusUrl, datasetId);
}

async function updateProgress(progress, statusUrl, datasetId) {
    var result = await $.getJSON(statusUrl);
    
    result.progress = progress;
    $(`#dataset-${datasetId}-progress-bar`).progressbar({"value": result.progress});
    $(`#dataset-${datasetId}-progress`).text(`${result.progress} %`);
    $(`#dataset-${datasetId}-status`).text(`${result.status} : ${result.progress} %`);
    
    if (progress++ < 100) {
        await timeout(500);
        updateProgress(progress, statusUrl, datasetId);
    }
}

function startChecker(datasetId) {
    // if dataset already running
    if ($(`#dataset-${datasetId}-completed`)[0].childNodes[1].classList[1] !== "fa-check-circle" ) {
        throw "Dataset hasn't been completed!";
    }
    console.log("Working!");
    // $.post(`/checkerstart/dataset${datasetId}`, {})
    //     .done( function(retJson) {

    //     }).fail( () => {
    //         alert('Failed to start checker for dataset '+datasetId);
    //     });
    initRunningProgress(datasetId);
}

async function main() {
    try {
        var datasetIds = await collectDatasetIds();
        console.log('Datasets ids: [' + datasetIds.join(', ') + ']');
        var runningDatasets = await getRunningDatasets(datasetIds);
        console.log('Running Datasets: [' + runningDatasets.join(', ') + ']');
        for (idx in runningDatasets) {
            console.log(idx);
            initRunningProgress(idx);
        }
        // Run monitoring of datasets
        for (idy in runningDatasets) {
            console.log(idy);
            launchMonitoring(idy);
        }
    } catch(err) {
        console.log(err);
    }   
}

main();