
function fix_headers(){
    if ($(document).scrollTop() > window._rubion_positions['header']['top']){
	if (! window._rubion_isfixed) {
	    $('header').css('position', 'fixed');
	    $('header').css('top', '0px');
	    $('header').css('z-index', 700);
	    $('header').css('width', window._rubion_positions['header']['width']);
	    $('.result-list thead').css('position', 'fixed');
	    $('.result-list thead').css('z-index', 700);
	    $('.result-list thead').css('width', window._rubion_positions['tabhead']['width']);
	    var count = 0;
	    $('.result-list thead th').each( 
		function(){
		    $(this).css('width',window._rubion_positions['thwidths'][count]);
		    count ++;
		}
	    );
	    count = 0;
	    var n_items = window._rubion_positions['thwidths'].length;
	    $('.result-list tbody td').each(
		function(){
		    $(this).css('width',
				window._rubion_positions['thwidths'][count % n_items]
			       );
		    count ++;
		}

	    );
	    $('header').next().css('margin-top',
		window._rubion_positions['header']['height']+'px');
	    $('.result-list table').css('margin-top', window._rubion_positions['tabhead']['height']+'px');
	    $('.result-list thead').css('top',window._rubion_positions['header']['height']+'px');
	    window._rubion_isfixed = true;
	} 
    }
    else {
	if (window._rubion_isfixed){
	    $('header').css('position','relative');
	    $('.result-list thead').css('position', 'relative');
	    $('.result-list table').css('margin-top', window._rubion_positions['table']['margin-top']);
	    $('header').next().css('margin-top','0px');

	    window._rubion_isfixed = false;
	}
    }
}

function compute_header_positions(){

    var p = {};

    p['header'] = $('header').position();
    p['header']['width'] = $('header').css('width');
    p['header']['height'] = $('header').outerHeight(true);
    p['tabhead'] = {
	'width': $('.result-list thead').css('width'),
	'height': $('.result-list thead').outerHeight(true)
    }
    p['thwidths'] = [];
    $('.result-list thead th').each(
	function(){
	    p['thwidths'].push($(this).css('width'));
	}
    );
    p['table']={
	'margin-top' : $('.result-list table').css('margin-top')
    }
    window._rubion_positions = p;
    window._rubion_isfixed = false;
}


$(document).ready(function(){
    compute_header_positions();
    $( window ).resize(function(){
	compute_header_positions();
	window._rubion_isfixed = false;
	fix_headers();
    });
    $(document).on('scroll', fix_headers);

});
