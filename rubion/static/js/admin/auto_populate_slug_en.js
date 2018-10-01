function initSlugAutoPopulate_en() {

    if ( $('#id_title').length > 0 )
	return
    var slugFollowsTitle = false;    
    $('#id_title_en').on('focus', function() {
        /* slug should only follow the title field if its value matched the title's value at the time of focus */
        var currentSlug = $('#id_slug').val();
        var slugifiedTitle = cleanForSlug(this.value, true);
        slugFollowsTitle = (currentSlug == slugifiedTitle);
    });

    $('#id_title_en').on('keyup keydown keypress blur', function() {
        if (slugFollowsTitle) {
            var slugifiedTitle = cleanForSlug(this.value, true);
            $('#id_slug').val(slugifiedTitle);
        }
    });
}
$(function() {
    /* Only non-live pages should auto-populate the slug from the title */
    if (!$('body').hasClass('page-is-live')) {
        initSlugAutoPopulate_en();
    }
});
