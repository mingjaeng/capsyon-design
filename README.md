<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Company Report Dashboard</title>
  <style>
    body {
      font-family: Arial, sans-serif;
      margin: 0; padding: 0;
      background-color: #f4f4f4;
    }
    header {
      background-color: #1e293b;
      color: white;
      padding: 1em;
      text-align: center;
    }
    .container {
      padding: 2em;
    }
    .report-card {
      background-color: white;
      padding: 1.5em;
      margin: 1em 0;
      border-radius: 8px;
      box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    .report-title {
      font-size: 1.2em;
      font-weight: bold;
    }
    .report-detail {
      color: #555;
      margin-top: 0.5em;
    }
  </style>
</head>
<body>
  <header>
    <h1>중소기업 리포트 대시보드</h1>
  </header>
  <div class="container">
    <div class="report-card">
      <div class="report-title">[기업명] 스마트솔루션</div>
      <div class="report-detail">산업: IT | 지역: 서울 | 설립: 2015년</div>
    </div>
    <div class="report-card">
      <div class="report-title">[기업명] 그린테크</div>
      <div class="report-detail">산업: 에너지 | 지역: 대전 | 설립: 2012년</div>
    </div>
  </div>
</body>
</html>
