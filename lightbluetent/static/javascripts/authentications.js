$(document).ready(function() {

    if ($("input[name='authentication']:checked").val() == "password") {
        var auth_type = "password";
        $("div.auth-box").hide();
        $("#auth_box_"+auth_type).show();
    }

    if ($("input[name='authentication']:checked").val() == "whitelist") {
        var auth_type = "whitelist";
        $("div.auth-box").hide();
        $("#auth_box_"+auth_type).show();
    }

    $('input[type="radio"]').change(function() {
    	var auth_type = $(this).val();
        $("div.auth-box").hide();
        $("#auth_box_"+auth_type).show();
    });
});
