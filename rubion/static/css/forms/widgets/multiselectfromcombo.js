if (!window.multiselectfromcombo){
    $(document).ready(function(){
	function sort_li(a, b) {
	    return $(b).children('label').html() < $(a).children('label').html() ? 1 : -1;
	}
	
	$('.multiselectfromcombo-outer').each(function(){
	    var self = this,
		ul_available = $(self).find('ul.available-items'),
		ul_selected = $(self).find('ul.selected-items');
	    
	    $(self).find('.sort-selected').click(function(){
		ul_selected.children('li').sort(sort_li).appendTo(ul_selected);
		return false;
	    });
	    
	    $(self).find('.inputcontainer input[type=checkbox]').each(function(){
		var ipt = this,
		    lbl = $('#'+$(ipt).attr('id')+'_label'),
		    lbl_li = lbl.parents('li').first();
		
		lbl_li.appendTo(ipt.checked ? ul_selected : ul_available);
		$(ipt).click(function(){
		    lbl_li.appendTo(ipt.checked ? ul_selected : ul_available);
		    if (! ipt.checked) {
			ul_available.children('li').sort(sort_li).appendTo(ul_available);
		    }
		});
	    });
	    ul_available.children('li').sort(sort_li).appendTo(ul_available);
	    $(self).find('.multiselectfromcombo-search').each(function(){
		var inputfield = this;
		$(inputfield).keypress(function(evt){
		    if (evt.which == 13) {
			evt.preventDefault();
		    }
		});
		$(inputfield).keyup(function(evt){
		    var val = $(inputfield).prop('value');
		    if (evt.which == 13) {
			evt.preventDefault();
			var child = $(ul_available).children('li:visible');
			if (child.length == 1){
			    $('#'+child.children('label').attr('for')).prop('checked',true);
			    child.appendTo(ul_selected)
				.children('label').css('background','transparent');
			    $(inputfield)
				.css('background','transparent')
				.css('font-weight','normal')
				.css('color','rgb(38, 38, 38)')
				.prop('value','')
				.keyup();
			}
			else {

			}
			
		    }
		    else {
			$(ul_available).children('li').each(
			    function(){
				var label = $(this).children('label');
				var reg = new RegExp(val, 'i');
				if (label.html().match(reg)){
				    $(this).show();
				}
				else {
				    $(this).hide();
				}
			    }
			);
			var vis = $(ul_available).children('li:visible');
			
			
			if (vis.length == 1){
			    vis.children('label').css('background','#189370');
			    $(inputfield).css('background','#189370')
				.css('color','#fff')
				.css('font-weight','bold')
			    ;
			}
			else {
			    vis.children('label').css('background','transparent');
			    $(inputfield).css('background','transparent')
				.css('color','rgb(38, 38, 38)')
				.css('font-weight','normal')
			    ;
			
			}
		    }
		});
	    });
	});
	
    }); // end ready
}

window.multiselectfromcombo = true;

