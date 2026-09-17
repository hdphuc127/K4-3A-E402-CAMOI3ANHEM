param(
    [string]$ApiBaseUrl = $env:VITE_API_BASE_URL,
    [int]$ModuleId = 1
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($ApiBaseUrl)) {
    $ApiBaseUrl = "http://127.0.0.1:8000/api/v1"
}

$ApiBaseUrl = $ApiBaseUrl.TrimEnd("/")

function Assert-True {
    param(
        [bool]$Condition,
        [string]$Message
    )

    if (-not $Condition) {
        throw "ASSERT FAILED: $Message"
    }
}

function Invoke-JsonApi {
    param(
        [string]$Method,
        [string]$Path,
        [object]$Body = $null
    )

    $uri = "$ApiBaseUrl$Path"
    if ($null -eq $Body) {
        return Invoke-RestMethod -Method $Method -Uri $uri -Headers @{ Accept = "application/json" }
    }

    return Invoke-RestMethod `
        -Method $Method `
        -Uri $uri `
        -Headers @{ Accept = "application/json" } `
        -ContentType "application/json" `
        -Body ($Body | ConvertTo-Json -Depth 12)
}

Write-Host "Frontend API workflow"
Write-Host "API base: $ApiBaseUrl"
Write-Host ""

Write-Host "1. Health check"
$health = Invoke-JsonApi -Method Get -Path "/health"
Assert-True $health.success "GET /health must return success=true"
Assert-True ($health.data.status -eq "ok") "GET /health data.status must be ok"
Write-Host "   OK: $($health.data.service) is $($health.data.status)"

Write-Host "2. Review data for main flow"
$reviewData = Invoke-JsonApi -Method Get -Path "/review-data"
Assert-True $reviewData.success "GET /review-data must return success=true"
Assert-True ($reviewData.data.weeks.Count -gt 0) "review-data must include weeks"
Assert-True ($reviewData.data.questions.Count -gt 0) "review-data must include questions"
Assert-True ($null -ne $reviewData.data.topics) "review-data must include topics"
Write-Host "   OK: weeks=$($reviewData.data.weeks.Count), questions=$($reviewData.data.questions.Count)"

Write-Host "3. Modules"
$modules = Invoke-JsonApi -Method Get -Path "/modules"
Assert-True $modules.success "GET /modules must return success=true"
Assert-True ($modules.data.Count -gt 0) "modules must not be empty"
$firstModule = $modules.data | Select-Object -First 1
if ($ModuleId -le 0) {
    $ModuleId = [int]$firstModule.id
}
Write-Host "   OK: modules=$($modules.data.Count), first=$($firstModule.title)"

Write-Host "4. Concepts for module $ModuleId"
$concepts = Invoke-JsonApi -Method Get -Path "/modules/$ModuleId/concepts"
Assert-True $concepts.success "GET /modules/{module_id}/concepts must return success=true"
Assert-True ($null -ne $concepts.data.module) "concepts response must include module"
Assert-True ($null -ne $concepts.data.concepts) "concepts response must include concepts array"
Write-Host "   OK: module=$($concepts.data.module.title), concepts=$($concepts.data.concepts.Count)"

Write-Host "5. Diagnosis used by Submit test button"
$diagnosisBody = @{
    lesson_id = "embedding"
    question_id = "q2"
    question_text = "Token ID 105 va 106 nam canh nhau. Dieu do noi len gi ve y nghia cua chung?"
    correct_answer = "Khong noi len dieu gi ve y nghia"
    student_answer = "Chung co y nghia gan nhau"
}
$diagnosis = Invoke-JsonApi -Method Post -Path "/diagnosis" -Body $diagnosisBody
Assert-True $diagnosis.success "POST /diagnosis must return success=true"
Assert-True ($diagnosis.data.question_id -eq "q2") "diagnosis must echo question_id"
Assert-True (-not [string]::IsNullOrWhiteSpace($diagnosis.data.hint)) "diagnosis must include hint"
Assert-True ($null -ne $diagnosis.data.citations) "diagnosis must include citations array"
Write-Host "   OK: is_correct=$($diagnosis.data.is_correct), citations=$($diagnosis.data.citations.Count)"

Write-Host ""
Write-Host "Workflow passed. Frontend can call the backend APIs used in the MVP flow."
