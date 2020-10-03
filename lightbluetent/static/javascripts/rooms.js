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
    if (!$(this).is(":checked")) aliasInput.val("")
});

/* Show the correct limit box on page load */
$('.limit_option').hide();
var value = $('#limit_select').val();
if (value == "until") {
    $('#limit_box_until').show();
} else if (value == "count") {
    $('#limit_box_count').show();
}

/* Show the auth div if the values change */
$('input[type="radio"]').change(function () {
    var auth_type = $(this).val();
    $("div.auth-box").hide();
    $("#auth_box_" + auth_type).show();
});

$('input[type="checkbox"]').click(function () {

    /* Show or hide the recurrence settings */
    if (this.id == "recurring_checkbox") {
        if ($(this).is(":checked")) {
            $("#recurring_box").show();
        } else {
            $("#recurring_box").hide();
        }
    }
});

/* Show the recurrence settings if they're selected on page load */
if ($("#recurring_checkbox").is(":checked")) {
    $("#recurring_box").show();
} else {
    $("#recurring_box").hide();
}

/* Enable the alias input if selected on page load */
if ($("alias_checkbox").checked) {
    $("alias_input").disabled = false;
} else {
    $("alias_input").disabled = true;
}

/* Show or hide the limit settings when the select changes */
$('#limit_select').change(function () {
    $('.limit_option').hide();
    var value = $(this).val();
    if (value == "until") {
        $('#limit_box_until').show();
    } else if (value == "count") {
        $('#limit_box_count').show();
    }
});

let sortable = new Sortable(document.querySelector("#links-list"), {
    handle: ".lbt-draggable",
    animation: 200,
    store: {
        get: function (sortable) {
            let order = String($('#links-list').data('links-order'));
            console.log(order);
            order = order ? order.split('|') : [];
            return order;
        },
        set: function (sortable) {
            const list = $('#links-list');
            let order = sortable.toArray();
            const token = list.data('csrf')
            $.ajax({
                type: "POST",
                url: list.data('path'),
                data: JSON.stringify({order}),
                dataType: 'json',
                contentType: 'application/json',
                headers: {
                    'X-CSRFToken': token
                },
            })
        },
    },
})