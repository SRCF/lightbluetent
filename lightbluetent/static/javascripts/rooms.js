// store the currently selected tab in the hash value
$("#nav-tab a").on("shown.bs.tab", function (e) {
    let id = $(e.target).attr("href");
    window.sessionStorage.setItem('last-tab', id)
});

// on load of the page: switch to the currently selected tab
$(`#nav-tab a[href="${window.sessionStorage.getItem('last-tab')}"]`).tab('show');

/* Show the password div if that's selected on page load */
if ($("input[name='authentication']:checked").val() == "password") {
    $("div.auth-box").hide();
    $("#auth_box_password").show();
}

/* Show the whitelist div if that's selected on page load */
if ($("input[name='authentication']:checked").val() == "whitelist") {
    $("div.auth-box").hide();
    $("#auth_box_whitelist").show();
}

/* Show the correct div if the values change */
$('input[type="radio"]').change(function () {
    var auth_type = $(this).val();
    $("div.auth-box").hide();
    $("#auth_box_" + auth_type).show();
});

/* Enable or disable the alias box */
$('#alias_checkbox').click(function () {
    let aliasInput = $('#alias_input');
    aliasInput.prop("disabled", !$(this).is(":checked"));
    if(!$(this).is(":checked")) aliasInput.val("")
});

/* Enable the alias input if selected on page load */
var alias_checkbox = document.getElementById("alias_checkbox")
var alias_input = document.getElementById("alias_input")
if (alias_checkbox.checked) {
    alias_input.disabled = false;
} else {
    alias_input.disabled = true;
}

/* Show the correct limit box on page load */
$('.limit_option').hide();
var value = $('#limit_select').val();
if (value == "until") {
    $('#limit_box_until').show();
} else if (value == "number") {
    $('#limit_box_number').show();
}

/* Show the auth div if the values change */
$('input[type="radio"]').change(function() {
 	var auth_type = $(this).val();
    $("div.auth-box").hide();
    $("#auth_box_"+auth_type).show();
});

$('input[type="checkbox"]').click(function() {

    /* Show or hide the recurrence settings */
    if (this.id == "recurring_checkbox") {
        if ($(this).is(":checked")) {
            $("#recurring_box").show();
        } else {
            $("#recurring_box").hide();
        }
    }
});

/* Show or hide the limit settings when the select changes */
$('#limit_select').change(function() {
    $('.limit_option').hide();
    var value = $(this).val();
    if (value == "until") {
        $('#limit_box_until').show();
    } else if (value == "number") {
        $('#limit_box_number').show();
    }
});

