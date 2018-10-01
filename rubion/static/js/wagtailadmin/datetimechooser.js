function hideCurrent(current, input) {
    var selected = new Date(input[0].value);
    if (!dateEqual(selected, current)) {
        $(this).find('.xdsoft_datepicker .xdsoft_current:not(.xdsoft_today)').removeClass('xdsoft_current');
    }
}
function initDateTimeChooser(id, opts) {
    if (window.dateTimePickerTranslations) {
        $('#' + id).datetimepicker($.extend({
            closeOnDateSelect: true,
            format: 'Y-m-d H:i',
            scrollInput: false,
            i18n: {
                lang: window.dateTimePickerTranslations
            },
            lang: 'lang',
            onGenerate: hideCurrent
        }, opts || {}));
    } else {
        $('#' + id).datetimepicker($.extend({
            format: 'Y-m-d H:i',
            onGenerate: hideCurrent
        }, opts || {}));
    }
}
function dateEqual(x, y) {
    return x.getDate() === y.getDate() &&
           x.getMonth() === y.getMonth() &&
           x.getYear() === y.getYear()
}
