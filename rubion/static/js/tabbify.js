(function (root, factory) {
    if ( typeof define === 'function' && define.amd ) {
	define([], factory(root));
    } else if ( typeof exports === 'object' ) {
	module.exports = factory(root);
    } else {
	root.tabbify = factory(root);
    }
})(typeof global !== 'undefined' ? global : this.window || this.global, function (root) {
    
    'use strict';
    
    //
    // Variables
    //
    
    var tabbify = {}; // Object for public APIs
    var supports = 'querySelector' in document && 'addEventListener' in root && 'classList' in document.createElement('_') && 'onhashchange' in root; // Feature test
    var settings, tab;

    var newElem = function(e, cls) {
	var elem = document.createElement(e);
	elem.classList.add(cls);
	return elem;
    }
    
    var activate = function( e ){
	var elem = e.target;
	activate_by_element( elem )
    }

    var activate_by_element= function( elem ){
	var all_buttons = elem.parentNode.getElementsByClassName('tab-button');
	var all_fields  = elem.parentNode.parentNode.getElementsByClassName('tab-content')[0].getElementsByTagName('fieldset');
	for (var i=0; i < all_buttons.length; i++){
	    all_buttons[i].classList.remove('active');
	    all_fields[i].classList.remove('active');
	}
	elem.classList.add('active');
	document.getElementById(elem.getAttribute('data-target')).classList.add('active');
    }
    

    tabbify.init = function( fs, title, all = false ) {
	if ( fs.length < 2 ) return;
	var elements = [];
	for (var i=0; i < fs.length; ++i){
	    elements[i] = document.getElementById('fieldset-'+fs[i]);
	}

	var tabLabel = newElem('span', 'tab-label');
	tabLabel.innerHTML = (all ? 'Fill all' : 'Choose one')+':';
	var container = newElem('div','tab-container');
	var buttonContainer = newElem('div','tab-buttons');
	var contentContainer = newElem('div','tab-content');
	var titleElem = newElem('span', 'legend');
	titleElem.innerHTML = title;
	buttonContainer.appendChild(titleElem);
	elements[0].parentNode.insertBefore( container, elements[0] );
	container.appendChild( buttonContainer );
	container.appendChild( contentContainer );
	var tmp, tmpElem, to_activate;
	for (i=0; i < fs.length; i++){
	    tmpElem = newElem('span','tab-button');
	    if (i==0) to_activate = tmpElem;
	    tmpElem.setAttribute('id','tab-button-'+fs[i]);
	    tmpElem.setAttribute('data-target','fieldset-'+fs[i]);
	    tmp = document.getElementById('legend-'+fs[i]);
	    tmpElem.innerHTML = tmp.innerHTML;
	    tmpElem.addEventListener('click', activate);
	    buttonContainer.appendChild(tmpElem);
	    contentContainer.appendChild(elements[i]);
	}
	buttonContainer.appendChild(tabLabel);
	activate_by_element(to_activate);
    };

    
    return tabbify;

});
