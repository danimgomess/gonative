<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Ticket Verification</title>
    <script src="script.js"></script>
    <link rel="stylesheet" href="styles.css" />
</head>

<?php
$code = $_GET['code'];
$id = $_GET['id'];
?>

<body style="text-align:center" onload="initializePage('<?php echo $code; ?>', <?php echo $id; ?>)">

    <img src="logo.png" alt="GoNative Logo" height='120' width='500'>

    <h2>Ticket verification for event:</h2>

    <div class='event'></div>

    <hr style="border: 1px solid black; width : 50%">

    <p>Ticket number: <?php echo $code ?></p>

    <div class='result'></div><br>

    <div class='use'>
        <button type="button" class="button" onclick="useTicket(<?php echo $id; ?>)">Mark Ticket As Used</button>'
    </div>

</body>

</html>