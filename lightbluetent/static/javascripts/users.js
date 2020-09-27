// update user setting via AJAX
function submitProfileChange(paths, data, token) {
    $.ajax({
        type: "POST",
        url: paths.success,
        data: JSON.stringify(data),
        dataType: 'json',
        contentType: 'application/json',
        headers: {
            'X-CSRFToken': token
        },
    }).done(function () {
        window.location.reload();
    }).fail(function (res, status, error) {
        $.ajax({
            type: "POST",
            url: paths.error,
            data: JSON.stringify({ code: res.status, name: error }),
            dataType: 'json',
            contentType: 'application/json',
            headers: {
                'X-CSRFToken': token
            }
        }).done(function () {
            window.location.reload();
        })
    });
}

// update user profile field
$('#profile-fields').on('click', 'button', function () {
    const paths = {
        success: $(this).data('path'), error: $(this).data('path-error')
    };
    const type = $(this).data('field-type');
    const data = { type, value: $(`#${type}-input`).val() };
    const token = $(this).data('csrf');
    submitProfileChange(paths, data, token)
});
