// 차트에서 포인트 갯수를 정의합니다
window.checked = new Array;
window.chart_chains = new Array;
window.chart = new Array;
window.form_opened = new Array;
window.itemsets = [];
window.items = {};
window.serverlist = [];
window.socket = 0;

function init(cnum, is, isc, u, uc, ih, sv){
	//alert('hahaha');
	window.chart_column_num = cnum;
	window.cur_itemset = is;
	window.cur_itemset_code = isc;
	window.cur_user = u;
	window.cur_user_code = uc;
	window.img_host = ih;
	window.server = sv;
	for (let i=0;i<6;i++) {
		form_opened[i] = 0;
	}
}
function modal_createid(){
	$('#modal_createid').on('shown.bs.modal', function () {
		$('#input-createid').focus();
	});
	$('#modal_createid').modal();
}
function modal_login(){
	$('#modal_login').on('shown.bs.modal', function () {
		$('#input-login').focus();
	});
	$('#modal_login').modal();
}
function modal_logout(){
	modalLogout.Show(cur_user);
}
function show_item_form(num) {
	//alert(document.getElementById('div-form-item'+num).style.display);
	if(form_opened[num]){
		closeForm(num);
	}
	else {
		openForm(num);
	}
}
function logouted() {
	// 로그인 버튼을 변경해줍니다
	document.getElementById("div-btn-loginned").style.display = "none";
}
function loginned() {
	// 로그인 버튼을 변경해줍니다
	document.getElementById("div-btn-loginned").style.display = "flex";
}
function submit_createid_form() {
	show_spinner();
	var name = document.getElementById('input-createid').value;
	var xhttp = new XMLHttpRequest();
	xhttp.onreadystatechange = function() {
		if (this.readyState == 4 && this.status == 200) {
			var data = JSON.parse(this.responseText);
			if(data.success == '1') {
				document.getElementById('input-createid').value = '';
				$('#modal_createid').modal('hide');
				code = data.code;
				cur_user_code = code;
				cur_itemset_code = 'default';
				//window.history.pushState('', '', '/u/' + cur_user_code + '/default');
				cur_user = data.name;
				rq_itemsets(function (){change_itemset(cur_user);});
				loginned();
			}
			else {
				$('#modal_createid').modal('hide');
				show_modal_login_confirm(data.name);
				//setTimeout(function (){$('#modal_createid').modal();}, 1000);
			}
			hide_spinner();
		}
	};
	xhttp.open("GET", '/create_user/' + name , true);
	xhttp.send();
}

function submit_login_form(str='') {
	show_spinner();
	var name = '';
	if(str) {
		name = str;
	}
	else {
		name = document.getElementById('input-login').value;
	}
	var xhttp = new XMLHttpRequest();
	xhttp.onreadystatechange = function() {
		if (this.readyState == 4 && this.status == 200) {
			var data = JSON.parse(this.responseText);
			if(data.success == '1') {
				document.getElementById('input-login').value = '';
				$('#modal_login').modal('hide');
				cur_user_code = data.code;
				cur_user = data.name;
				itemsets = data.itemsets;
				update_itemset_dropdown();
				// 해당아이디의 디폴트 세트명은 유저이름이라
				change_itemset(cur_user);	
				//rq_itemsets(function (){change_itemset(cur_user);});
				loginned();
			}
			else {
				$('#modal_login').modal('hide');
				//show_modal_info('없는 사용자입니다', 1100);
				modalInfo.Show('없는 사용자입니다', 1100);
				setTimeout(function (){$('#modal_login').modal();}, 1000);
			}
			hide_spinner();
		}
	};
	xhttp.open("GET", '/login/' + name , true);
	xhttp.send();
}
function submit_item_form(num) {
	//alert('div-form-item'+num);
	//alert(document.getElementById('div-form-item'+num).style.display);
	closeForm(num);
	var i_name = document.getElementById('input-item'+num).value;
	i_name = i_name.trim();
	if(i_name) {
		// vanilla js 를 이용해봅니다
		var xhttp = new XMLHttpRequest();
		xhttp.onreadystatechange = function() {
			if(this.readyState == 4 && this.status == 200) {
				var data = JSON.parse(this.responseText);
				if(data.success) {
					update_item_area(data.num, data.indiv_ar);
				}
				else {
					modalInfo.Show('없는 아이템입니다', 800);
					setTimeout(function (){openForm(num);}, 900);
				}
			}
		};
		fullstr = collect_items_tostring(num, i_name);
		var dummy = new Date().getTime();
		xhttp.open("GET", '/update_indiv/' + num + '/' + server + '/' + cur_user 
						+ '/' + cur_itemset + '/' + i_name + '/' + fullstr + '/' + dummy,true);
		xhttp.send();
	}
}
function submit_itemset_form(num) {
	closeSetForm();
	var s_name = document.getElementById('input-itemset').value;
	s_name = s_name.trim();
	if(s_name) {
		//vanilla js 를 이용해봅니다
		var xhttp = new XMLHttpRequest();
		xhttp.onreadystatechange = function() {
			if(this.readyState == 4 && this.status == 200) {
				var data = JSON.parse(this.responseText);
				if(data.success == '1') {
					// 생성성공하였을 경우 처리합니다
					document.getElementById('input-itemset').value = '';
					// callback을 추가하여 itemsets 업데이트 후 해당이름의 아이템으로 change합니다
					rq_itemsets(function () {change_itemset(s_name);});
					//change_itemset(s_name);
				}
				else if (data.success == '0') {
					alert('이미 있는 세트명입니다');
				}
			}
		};
		xhttp.open("GET", '/create_itemset/' + cur_user + '/' + s_name, true);
		xhttp.send();
	}
}

function update_chart(a, b) {
	var checked = window.checked;
	if(checked[a] != b){
		checked[a] = b;
		min_chain_ = window.chart_chains[a];
		var data_ = [],
			len_ = min_chain_.length;
		//30분 주기일 경우
		if(b == 0){
			for (let j=len_ - chart_column_num;j<=len_ - 1;j++){
				data_.push(min_chain_[j] / 10000);
			}
			var labels_ = [];
			for(let l_=0;l_<chart_column_num;l_++){
				labels_.push("");
			}
		}
		//60분 주기일 경우
		else if(b == 1){
			for (let j=len_ - chart_column_num*2 + 1;j<=len_ - 1;j+=2){
				data_.push(min_chain_[j] / 10000);
			}
			var labels_ = [];
			for(let l_=0;l_<chart_column_num;l_++){
				labels_.push("");
			}
		}
		//60*2분 주기일 경우
		else if(b == 2){
			for (let j=len_ - chart_column_num*4 + 3;j<=len_ - 1;j+=4){
				data_.push(min_chain_[j] / 10000);
			}
			var labels_ = [];
			for(let l_=0;l_<chart_column_num;l_++){
				labels_.push("");
			}
		}
		//30*2*7(=420)분 주기일 경우
		else if(b == 3){
			for (let j=len_ - chart_column_num*14 + 13;j<=len_ - 1;j+=14){
				data_.push(min_chain_[j] / 10000);
			}
			var labels_ = [];
			for(let l_=0;l_<chart_column_num;l_++){
				labels_.push("");
			}
		}
		//30*2*24(=1440)분 주기일 경우
		//30*2*30(=1800)분 주기일 경우
		else if(b == 4){
			//for (let j=len_ - chart_column_num*48 + 47;j<=len_ - 1;j+=48){
			for (let j=len_ - chart_column_num*60 + 59;j<=len_ - 1;j+=60){
				data_.push(min_chain_[j] / 10000);
			}
			var labels_ = [];
			for(let l_=0;l_<chart_column_num;l_++){
				labels_.push("");
			}
		}
		//eval('chart'+a).data.labels = labels_;
		//eval('chart'+a).data.datasets[0].data = data_;
		//eval('chart'+a).update();
		chart[a].data.labels = labels_;
		chart[a].data.datasets[0].data = data_;
		chart[a].update();
	}
}
function setupWebSocket(){
	this.socket = new WebSocket('wss://'+window.location.host+'/ws');
	//this.socket = new WebSocket('ws://'+window.location.host+'/ws');
	this.socket.onopen = function(){
		socket.send('connect');
	}
	this.socket.onclose = function(){
		setTimeout(setupWebSocket, 1000);
	}
	// 서버로부터 update 문자열이 들어왔을 경우
	this.socket.onmessage = function(msg){
		if (msg.data == 'update'){
			rq_dumptime();
			rq_itemset(cur_itemset);
			rq_itemsets();
			/*	
			var xhttp = new XMLHttpRequest();
			xhttp.onreadystatechange = function() {
				if (this.readyState == 4 && this.status == 200) {
					var data = JSON.parse(this.responseText);
					update_page(data);
				}
			};
			var dummy = new Date().getTime();
			xhttp.open("GET", '/update/' + server + '/' + \
								cur_user + '/' + cur_itemset + '/' + dummy, true);
			xhttp.send();
			//$.getJSON('/update/' + server + '/' + cur_itemset, function(data){update_page(data);});
			*/
		}
	}
}	

function create_itemset() {
	openSetForm();
}
function checkif_defaultset(itemset) {	
	var ret = 0;
	if((cur_user=='guest' && itemset == '기본구성') || (cur_user!='guest' && itemset==cur_user)) {
		ret = 1;
	}
	return ret;
}

function coloring_setbutton(cur_itemset) {
	//if((cur_user=='guest' && cur_itemset == '기본구성') || (cur_user!='guest' && cur_itemset==cur_user)) {
	if(checkif_defaultset(cur_itemset)) {
	//if(cur_set.trim() == '기본구성') {
		document.getElementById("button_itemset").className = 'btn btn-secondary btn-large btn-block dropdown-toggle text-warning';
	}
	else {
		document.getElementById("button_itemset").className = 'btn btn-secondary btn-large btn-block dropdown-toggle text-muted';
	}
}

function change_server(srver){
	// 이후 각 드롭다운 항목들을 새로 만들어 교체해줍니다
	show_spinner();
	window.server = srver;
	rq_itemset(cur_itemset);
	rq_dumptime();
	document.getElementById("div_serverlist").innerHTML = ""; 
	for(let i=0;i<serverlist.length;i++){
		// cur_itemset이 아닌 항목들만 추가합니다
		i_server = serverlist[i];
		if(i_server != server){
			document.getElementById("div_serverlist").innerHTML += 
				"<a id='server" + i + 
				"' class='dropdown-item text-center' href='javascript:;'" + 
				"onclick='change_server(\""+ i_server + "\")';>" + i_server + "</a>";
		}
	}
	// 혹시 아이템 입력창이 열려있을 수 있으므로 모두 닫습니다.
	for (let i=0;i<6;i++){
		closeForm(i);
	}
	
	document.getElementById("button_serverlist").innerHTML = 
		"<i class='fas fa-check-circle text-success'>&nbsp;</i>" + server;
}

function change_itemset(itemset){
	// 이후 각 드롭다운 항목들을 새로 만들어 교체해줍니다
	cur_itemset = itemset;
	document.getElementById("div_itemlist").innerHTML = ""; 
	ilen = itemsets.length;
	for(let it=0;it<ilen;it++){
		// cur_itemset이 아닌 항목들만 추가합니다
		if(itemsets[it] != itemset){
			document.getElementById("div_itemlist").innerHTML += 
		"<a id='itemlist" + it +"' class='dropdown-item text-center' href='javascript:;' onclick='change_itemset(\"" + itemsets[it] + "\");'>" + itemsets[it] + "</a>";
		}
	}
	if(checkif_defaultset(itemset)) {
	//if((cur_user=='guest' && itemset == '기본구성') || (cur_user!='guest' && itemset==cur_user)) {
		document.getElementById("button_itemset").innerHTML = 
		"<i class='far fa-file-alt' style='font-weight:lighter;font-size:1.0em'></i>&nbsp;&nbsp;" + itemset;
	}
	else {
		document.getElementById("button_itemset").innerHTML = itemset; 
	}
	coloring_setbutton(itemset);
	// 혹시 아이템 입력창이 열려있을 수 있으므로 모두 닫습니다.
	for (let i=0;i<6;i++){
		closeForm(i);
	}

	// xmlrequest 전송전 버튼색상을 변경합니다
	show_spinner();
	// 역시 vanilla js 로 변경해봅니다
	rq_itemset(itemset, function () {
			if(cur_user != 'guest') {
				window.history.pushState('', '', '/u/' + cur_user_code + '/' + cur_itemset_code);
			}
			update_itemset_dropdown();
	});
	//alert('in change_itemset: ' + cur_user + '/'+ cur_itemset_code +' 들와야하는디');
	//update_itemset_dropdown();
}

function progress_start(id_, color_){
	//document.getElementById(id_).style.WebkitTransition = "background 3.2s";
	document.getElementById(id_).style.transition = "background 3.2s";
	//document.getElementById(id_).style.transitionTimingFunction = "linear";
	document.getElementById(id_).style.transitionTimingFunction = "ease";
	//document.getElementById(id_).style.background = "#e74c3c"; // danger red
	//document.getElementById(id_).style.background = "#00bc8c"; // success mint
	document.getElementById(id_).style.background = color_; // info lightblue
	//document.getElementById(id_).style.WebkitTransform = "scale(1.2)"; // info lightblue
	//document.getElementById(id_).style.transform = "scale(1.2)"; // info lightblue
}
function progress_end(id_){
	document.getElementById(id_).style.WebkitTransition = "all 0.1s";
	document.getElementById(id_).style.transition = "all 0.1s";
	document.getElementById(id_).style.background = "#444444";
	//document.getElementById(id_).style.WebkitTransform = "scale(1.0)"; // info lightblue
	//document.getElementById(id_).style.transform = "scale(1.0)"; // info lightblue
}

// 개별 아이템 업그레이드 함수입니다
function update_indiv(data){
	var ar = data.indiv_ar;
	var i = data.num;
	if(!ar.name) return;
	document.getElementById("input-item"+i).value = '';
	document.getElementById("image"+i).setAttribute("style", "background-image: url('" + img_host + ar.image + ".jpg')"); 
	document.getElementById("itemname"+i).innerHTML = ar.name;
	document.getElementById("num"+i).innerHTML = ar.num;
	document.getElementById("moneygold"+i).innerHTML = ar.gold;
	document.getElementById("moneysilver"+i).innerHTML = ar.silver;
	document.getElementById("moneycopper"+i).innerHTML = ar.copper;
	document.getElementById("min_seller"+i).innerHTML = ar.min_seller;

	//실제로 클릭액션을 해야하는 클래스라 안먹힙니다
	//document.getElementById("lb"+i+"0").checked = 1; 
	document.getElementById("lb"+i+"0").click();
	
	// 아직chLine이 미처 생성되지 않았을 경우 exception이 발생해 이상동작이 발생하는듯 
	if(eval('chart'+i)){
		// chart_chain 전역배열변수에 일단 저장을 해야합니다
		chart_chains[i] = ar.min_chain;  
		min_chain_ = chart_chains[i];
		var data_ = [],
			len_ = min_chain_.length;
		//alert(min_chain_[0]);
		for (let j=len_ - chart_column_num;j<=len_ - 1;j++){
		//for (i=0;i<=3;i++){
			data_.push(min_chain_[j] / 10000);
		}
		var labels_ = [];
		for(let l_=0;l_<chart_column_num;l_++){
			labels_.push("");
		}
		eval('chart'+i).data.labels = labels_;
		eval('chart'+i).data.datasets[0].data = data_;
		eval('chart'+i).update();
	}
}

// itemsets의 제일 앞에 생성(+)를 삽입해 줍니다
function deco_itemsets() {
	if(itemsets[0] != ' 만들기') {
		itemsets.unshift(' 만들기');
	}
}

function update_itemset_dropdown() {
	deco_itemsets();
	// 이후 각 드롭다운 항목들을 새로 만들어 교체해줍니다
	document.getElementById("div_itemlist").innerHTML = ""; 
	
	// 새로만들기항목
	document.getElementById("div_itemlist").innerHTML += 
	"<a id='itemlist0' class='dropdown-item text-center font-weight-bolder text-info' href='javascript:;' onclick='create_itemset();'> <i class='fas fa-folder-open' style='font-weight:lighter;font-size:1.0em;'>&nbsp;</i>" + itemsets[0] + "</a>";
	// 아이템세트들
	window.dropdown_pair = {};
	for(let it=1;it<itemsets.length;it++){			//0이 아닌 1부터시작 
		// cur_itemset이 아닌 항목들만 추가합니다
		var cur = itemsets[it];
		if(cur != cur_itemset){
			//alert(cur + ',' + cur_user);
			if(checkif_defaultset(cur)) {
			//if((cur_user=='guest' && cur == '기본구성') || (cur_user!='guest' && cur==cur_user)) {
				document.getElementById("div_itemlist").innerHTML +=  
				"<a id='itemlist" + it +"' class='dropdown-item text-center text-warning' href='javascript:;' onclick='change_itemset(\"" + cur + "\");'><i class='far fa-file-alt' style='font-weight:lighter;font-size:1.0em'></i>&nbsp;&nbsp;" + cur + "</a>";
			}
			else {
				// 아이템명 뒤에 휴지통을 추가합니다
				dropdown_pair[it] = cur;
				document.getElementById("div_itemlist").innerHTML += 
					"<div id='dropdown-delete" + it + "' class='dropdown-delete'>" + 
					"<i class='far fa-trash-alt text-muted'></i></div>" +
					"<a id='itemlist" + it +"' class='dropdown-item text-center'" +
					"href='javascript:;' onclick='change_itemset(\"" + cur + "\");'>" + cur + "</a>";
			}
		}
	}
	// 위의 if-else 내에서 innerHTML 작성하면서 addeventlistener를 행하니 동작하지 않았습니다. 
	// 그래서 for loop 번거롭지만 별도로 뺐습니다.
	// 또한 inner function closure 문제 관련해서도 추후 별도의 함수선언으로 뺐습니다
	function fn_modal_delete(i) {
		return function () {show_modal_delete(dropdown_pair[i]);}
	}
	for(let it=1;it<itemsets.length;it++){			//0이 아닌 1부터시작 
		if(document.getElementById('dropdown-delete'+it)){
			//document.getElementById('dropdown-delete'+it).addEventListener("click", function(){
				//show_modal_delete(dropdown_pair[it]);}); 
			document.getElementById('dropdown-delete'+it).addEventListener("click", 
														fn_modal_delete(it));
		}
	}
	
	// 아이콘 데코레이션 작업
	if(checkif_defaultset(cur_itemset)) {
	//if((cur_user=='guest' && cur_itemset == '기본구성') || (cur_user!='guest' && cur_itemset==cur_user)) {
	//if(cur_itemset == '기본구성') {
		document.getElementById("button_itemset").innerHTML = "<i class='far fa-file-alt' style='font-weight:lighter;font-size:1.0em'></i>&nbsp;&nbsp;" + cur_itemset; 
	}
	else {
		document.getElementById("button_itemset").innerHTML = cur_itemset;
	}

	coloring_setbutton(cur_itemset);
}
//function update_dumped_time(data) {
function update_dumped_time(time) {
	//document.getElementById("dumped_at").innerHTML =  data.server + " DB dumped recently at &nbsp;";
	//document.getElementById("update_time").innerHTML = data.time;
	document.getElementById("dumped_at").innerHTML =  server + " DB dumped recently at ";
	document.getElementById("update_time").innerHTML = time;
}
function show_spinner() {
	//spinner show
	document.getElementById("div-spinner").style.display="flex";
	document.getElementById("div-srv-screener").style.display="flex";
	document.getElementById("div-login-screener").style.display="flex";
}
function hide_spinner() {
	//spinner 제거
	document.getElementById("div-spinner").style.display="none";
	document.getElementById("div-srv-screener").style.display="none";
	document.getElementById("div-login-screener").style.display="none";
}
function update_indiv_chart(n, min_chain) {
	// 아직chLine이 미처 생성되지 않았을 경우 exception이 발생해 이상동작이 발생하는듯 
	if(chart[n]){
		//min_chain_ = data[Object.keys(data)[i]].min_chain;
		chart_chains[n] = min_chain;
		min_chain_ = min_chain;
		//alert(min_chain_[min_chain_.length - 1]);
		//eval('chLine' + i).data = min_chain_[min_chain_.length - 1] / 10000;
		let data_ = [],
			len_ = min_chain_.length;
		//alert(min_chain_[0]);
		for (let j=len_ - chart_column_num;j<=len_ - 1;j++){
		//for (i=0;i<=3;i++){
			data_.push(min_chain_[j] / 10000);
		}
		var labels_ = [];
		for(let l_=0;l_<chart_column_num;l_++){
			labels_.push("");
		}
		//alert(data_[0]);
		//eval('chLine' + i).data = min_chain_.slice(,min_chain_.length - 1) / 10000);
		//eval('chart' + i).data = full_data_; 
		//eval('chart' + i).data.datasets[0].data = [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1]; 
		chart[n].data.labels = labels_;
		chart[n].data.datasets[0].data = data_;
		chart[n].update();
		//alert('엄지척');
	}
}

function update_charts(data) {
	// 아직chLine이 미처 생성되지 않았을 경우 exception이 발생해 이상동작이 발생하는듯 
	for(var i=0;i<6;i++) {
		//if(eval('chart'+i)){
		if(chart[i]){
			chart_chains[i] = data[i].min_chain;
			min_chain_ = chart_chains[i];
			let data_ = [],
				len_ = min_chain_.length;
			//alert(min_chain_[0]);
			for (let j=len_ - chart_column_num;j<=len_ - 1;j++){
			//for (i=0;i<=3;i++){
				data_.push(min_chain_[j] / 10000);
			}
			var labels_ = [];
			for(let l_=0;l_<chart_column_num;l_++){
				labels_.push("");
			}
			//eval('chart'+i).data.labels = labels_;
			//eval('chart'+i).data.datasets[0].data = data_;
			//eval('chart'+i).update();
			chart[i].data.labels = labels_;
			chart[i].data.datasets[0].data = data_;
			chart[i].update();
			//alert('엄지척');
			//eval('chLine' + i).addData = data_; 
			//eval('chLine' + i).update();
		}
	}
}
function update_serverlist() {
	document.getElementById("div_serverlist").innerHTML = ""; 
	for(let i=0;i<serverlist.length;i++){
		// cur_itemset이 아닌 항목들만 추가합니다
		i_server = serverlist[i];
		if(i_server != server){
			document.getElementById("div_serverlist").innerHTML += 
				"<a id='server" + i + "' class='dropdown-item text-center' href='javascript:;'" + 
				"onclick='change_server(\""+ i_server + "\")';>" + i_server + "</a>";
		}
	}
	// 혹시 아이템 입력창이 열려있을 수 있으므로 모두 닫습니다.
	//for (let i=0;i<6;i++){
		//closeForm(i);
	//}
}

function update_item_area(n, itemdata) {
	items[n] = itemdata.name;
	document.getElementById("input-item"+n).value = '';
	document.getElementById("image"+n).setAttribute("style", "background-image: url('" + img_host + itemdata.image + ".jpg')"); 
	document.getElementById("itemname"+n).innerHTML = itemdata.name;
	document.getElementById("num"+n).innerHTML = itemdata.num;
	document.getElementById("moneygold"+n).innerHTML = itemdata.gold;
	document.getElementById("moneysilver"+n).innerHTML = itemdata.silver;
	document.getElementById("moneycopper"+n).innerHTML = itemdata.copper;
	document.getElementById("min_seller"+n).innerHTML = itemdata.min_seller;

	//실제로 클릭액션을 해야하는 클래스라 안먹힙니다
	//document.getElementById("lb"+i+"0").checked = 1; 
	document.getElementById("lb"+n+"0").click();
	update_indiv_chart(n, itemdata.min_chain);
}


// 전체 6개 아이템 업데이트 함수입니다
function update_page(data){
	// data 갯수, 즉 6회동안 각 요소 갱신을 반복합니다
	show_spinner();
	t = data.time;
	itemsets = data.itemsets;
	serverlist = data.serverlist;
	data = data.ar;
	update_serverlist();
	// sort를 통해 아래와같이 할수도 있지만 이미 html상 해당id들이 정렬된채 생성된 상태라 상관없습니다
	for (let i=0;i < Object.keys(data).length;i++) {
		document.getElementById("image"+i).setAttribute("style", "background-image: url('" + img_host + data[i].image + ".jpg')"); 
		document.getElementById("itemname"+i).innerHTML = data[i].name;
		document.getElementById("num"+i).innerHTML = data[i].num;
		document.getElementById("moneygold"+i).innerHTML = data[i].gold;
		document.getElementById("moneysilver"+i).innerHTML = data[i].silver;
		document.getElementById("moneycopper"+i).innerHTML = data[i].copper;
		document.getElementById("min_seller"+i).innerHTML = data[i].min_seller;

		document.getElementById("lb"+i+"0").click();
		
	}
	update_charts(data);
	update_itemset_dropdown();
	hide_spinner();
} //function update_page() ends

/*
function show_modal_info(text, time) {
	modalInfo.text(text);
	modalInfo.show_time(time);
}
*/

function show_modal_delete(setname) {
	document.getElementById('delete_name').innerHTML = setname;
	$('#modal_delete').modal();
}
function show_modal_login_confirm(id) {
	document.getElementById('modal_login_create_confirm_text').innerHTML = id;
	$('#modal_login_with_createid').modal();
}

function login_with_createid_confirm() {
	$('#modal_login_with_createid').modal('hide');
	var id = document.getElementById('modal_login_create_confirm_text').innerHTML;
	submit_login_form(id); 
	document.getElementById('modal_login_create_confirm_text').innerHTML = '';
	document.getElementById('input-createid').value='';
}
function logout_confirm() {
	window.history.pushState('', '', '/');
	//submit_login_form('guest');
	cur_user = 'guest';
	cur_itemset = '기본구성';
	rq_itemset(cur_itemset);
	rq_itemsets();
	modalLogout.hide();
	logouted(); 
}

function delete_confirm() {
	setname = document.getElementById('delete_name').innerHTML;
	$('#modal_delete').modal('hide');
	// modal
	show_spinner();
	var xhttp = new XMLHttpRequest();
	xhttp.onreadystatechange = function() {
		if(this.readyState == 4) {
			hide_spinner();
			if (this.status == 200) {
				var data = JSON.parse(this.responseText);
				if(data.success == '1') {
					document.getElementById('input-itemset').value = '';
					// 아래 생성 주석과 달리 delete는 콜백으로 추가 아이템 선택 루틴이 필요없습니다
					// callback을 추가하여 itemsets 업데이트 후 해당이름의 아이템으로 change합니다
					rq_itemsets();
				}
				else if (data.success == '0') {
					//show_modal_info('이미 없는 세트명입니다', 1300);
					modalInfo.Show('이미 없는 세트명입니다', 1300);
					rq_itemsets();
					//alert('이미 없는 세트명입니다');
				}
			}
		}
	};
	xhttp.open("GET", '/delete_itemset/' + cur_user + '/' + setname ,true);
	xhttp.send();
}
function openLoginForm() {
	document.getElementById("input-login").focus();
	document.getElementById('icon-login-cancel').style.display = 'flex';
	document.getElementById('modal-createid-outer').style.display = 'none';
	document.getElementById('modal-login-outer').style.display = 'block';
}

function closeLoginForm() {
	$('#modal_login').modal('hide');
}
function closeLogoutForm() {
	$('#modal_logout').modal('hide');
}
function closeDeleteModal() {
	$('#modal_delete').modal('hide');
}
function closeCreateIDModal() {
	$('#modal_createid').modal('hide');
}
function closeLoginWithCreateIDModal() {
	$('#modal_login_with_createid').modal('hide');
}

function openSetForm() {
	document.getElementById("div-form-itemset").style.display = 'flex';
	document.getElementById("input-itemset").focus();
	document.getElementById('icon-set-cancel').style.display = 'flex';
}

function closeSetForm() {
	document.getElementById("div-form-itemset").style.display = 'none';
	document.getElementById('icon-set-cancel').style.display = 'none';
}

function closeForm(num) {
	document.getElementById('div-form-item'+num).style.display = 'none';
	document.getElementById('icon-cancel'+num).style.display = 'none';
	form_opened[num] = 0;
}
function openForm(num) {
	document.getElementById('div-form-item'+num).style.display = 'flex';
	document.getElementById("input-item"+num).focus();
	document.getElementById('icon-cancel'+num).style.display = 'flex';
	form_opened[num] = 1;
}

function letscreate() {
	$('#modal_login').modal('hide');
	modal_createid();
}

// was in DOMContentLoaded
if(window.addEventListener) {
	window.addEventListener("keydown", function (event) {
		//alert(event.key);
		// IE에선 Esc 입니다
		if(event.key == "Escape" || event.key == "Esc"){
			for(let i=0;i<6;i++) {
				closeForm(i);
			}
			closeSetForm();
			closeLoginForm();
			closeDeleteModal();
			closeCreateIDModal();
			closeLoginWithCreateIDModal();
			closeLogoutForm();
		}
	});
}
else if (document.attachEvent) { // IE 용으로 만들었는데 이문제가 아니었습니다. 또한IE10이상에서는
								// 해결된 문제로 보입니다
	document.attachEvent("keydown", function (event) {
		//alert(event.key);
		if(event.key == "Escape"){
			for(let i=0;i<6;i++) {
				closeForm(i);
			}
			closeSetForm();
			closeLoginForm();
		}
	});
}

document.getElementById('modal_login_with_createid').addEventListener('keydown', function (event) {
	if(event.key == "Enter"){
		login_with_createid_confirm();
	}
});
document.getElementById('modal_logout').addEventListener('keydown', function (event) {
	if(event.key == "Enter"){
		logout_confirm();
	}
});

// explorer 11 에서 let 이 제대로 지원안된다고 합니다.MDN에 따르면,
// function scope밖에 없으므로classic한 방법인 별도의 function에서 생성하는 방법을 택했습니다
// 참고:https://stackoverflow.com/questions/750486/javascript-closure-inside-loops-simple-practical-example?page=1&tab=votes#tab-top
function fn_update_chart(i,j) {
	return function () {update_chart(i, j);}
}
function fn_item_cancel(i) {
	return function () {
		if(document.getElementById("input-item"+i).value == '') {
			closeForm(i);
		}
		else {
			document.getElementById("input-item"+i).value=''; 
			document.getElementById("input-item"+i).focus();
		}
	}
}
for (let uu=0;uu<6;uu++) {
	checked[uu] = 0;
	document.getElementById('lb' + uu + '0').addEventListener('click', fn_update_chart(uu, 0), false);
	document.getElementById('lb' + uu + '1').addEventListener('click', fn_update_chart(uu, 1), false);
	document.getElementById('lb' + uu + '2').addEventListener('click', fn_update_chart(uu, 2), false);
	document.getElementById('lb' + uu + '3').addEventListener('click', fn_update_chart(uu, 3), false);
	document.getElementById('lb' + uu + '4').addEventListener('click', fn_update_chart(uu, 4), false);
	document.getElementById("icon-cancel"+uu).addEventListener('click', fn_item_cancel(uu), false);
}

document.getElementById("icon-set-cancel").addEventListener('click', function() { 
	t = document.getElementById("input-itemset").value; 
	if(t == '') {
		closeSetForm();
	}
	else {
		document.getElementById("input-itemset").value=''; 
		document.getElementById("input-itemset").focus();
	}
}, false);
document.getElementById("icon-login-cancel").addEventListener('click', function() { 
	tt = document.getElementById("input-login").value; 
	if(tt == '') {
		closeLoginForm();
	}
	else {
		document.getElementById("input-login").value=''; 
		document.getElementById("input-login").focus();
	}
}, false);
document.getElementById("icon-createid-cancel").addEventListener('click', function() { 
	tt = document.getElementById("input-createid").value; 
	if(tt == '') {
		closeCreateIDModal();
	}
	else {
		document.getElementById("input-createid").value=''; 
		document.getElementById("input-createid").focus();
	}
}, false);

function rq_itemsets(fn_callback) {
	// 역시 vanilla js 를 사용해 봅니다
	var xhttp = new XMLHttpRequest();
	xhttp.onreadystatechange = function() {
		if (this.readyState == 4 && this.status == 200) {
			var data = JSON.parse(this.responseText);
			itemsets = data.itemsets;
			update_itemset_dropdown();
			if(fn_callback) { 
				fn_callback();
			}
		}
	};
	var dummy = new Date().getTime();
	xhttp.open("GET", '/rq_itemsets/' + cur_user + '/' + dummy, true);
	xhttp.send();
}

function rq_itemset(itemset, fn_callback=0) {
	// 역시 vanilla js 를 사용해 봅니다
	var xhttp = new XMLHttpRequest();
	xhttp.onreadystatechange = function() {
		if (this.readyState == 4 && this.status == 200) {
			var data = JSON.parse(this.responseText);
			data_ = data.data
			l_ = Object.keys(data_);
			if(l_ < 5) {
				//alert('이미 삭제된 세트입니다');
				//show_modal_info('없는 세트명입니다', 1300);
				modalInfo.Show('없는 세트명입니다', 1300);
				setTimeout(rq_itemsets(function (){change_itemset('기본구성');}),100);
				//setTimeout(change_itemset('기본구성'),100);
			}
			else {
				s_ = l_.length;
				cur_itemset_code = data.code; 
				//alert('in rq_itemset:' + cur_itemset_code);
				//window.history.pushState('', '', '/u/' + cur_user_code + '/' + cur_itemset_code);
				for (let i=0;i < s_;i++) {
					rq_itemdata(i, data_[i]['item']);
				}
				if(fn_callback) {
					fn_callback();
				}
			}
		}
	};
	var dummy = new Date().getTime();
	xhttp.open("GET", '/rq_itemset/' + cur_user + '/' + itemset + '/' + dummy, true);
	xhttp.send();
}

function rq_itemdata(n, name) {
	var xhttp = new XMLHttpRequest();
	xhttp.onreadystatechange = function() {
		if (this.readyState == 4 && this.status == 200) {
			var data = JSON.parse(this.responseText);
			update_item_area(data.num, data.itemdata);
			// 모든 item이 갱신되지 않더라도 spinner를 숨기도록 합니다
			hide_spinner();
		}
	};
	//fullstr = collect_items_tostring(n, name);
	var dummy = new Date().getTime();
	xhttp.open("GET", '/rq_item/' + n + '/' + server + '/' + name + '/' + dummy, true);
	//xhttp.open("GET", '/rq_item/' + cur_user + '/' + n + '/' + server + '/' 
							//+ fullstr + '/' + dummy, true);
	xhttp.send();
}

function collect_items_tostring(n, name) {
	var str = '';
	for(let i=0;i<5;i++) {
		if(i==Number(n)) {
			str += name.trim();
		}
		else {
			str += document.getElementById('itemname'+i).innerHTML.trim();
		}
		str += ',';
	}
	str += document.getElementById('itemname5').innerHTML.trim();
	return str;
}

function rq_dumptime() {
	// 역시 vanilla js 를 사용해 봅니다
	var xhttp = new XMLHttpRequest();
	xhttp.onreadystatechange = function() {
		if (this.readyState == 4 && this.status == 200) {
			var data = JSON.parse(this.responseText);
			update_dumped_time(data.time);
		}
	};
	// 캐싱해도 괜찮은 컨텐츠입니다. dummy를 제거합니다
	//var dummy = new Date().getTime();
	xhttp.open("GET", '/rq_servertime/' + server , true);
	xhttp.send();
}

function rq_fullpage() {
	// 역시 vanilla js 를 사용해 봅니다
	var xhttp = new XMLHttpRequest();
	xhttp.onreadystatechange = function() {
		if (this.readyState == 4 && this.status == 200) {
			var data = JSON.parse(this.responseText);
			update_page(data);
		}
	};
	var dummy = new Date().getTime();
	xhttp.open("GET", '/update/' + server + '/' + 
						cur_user + '/' + cur_itemset + '/' + dummy, true);
	xhttp.send();
}

function login_btn_to_logout_btn() {
}

function create_chart_objects() {
	//window[eval('k'+1)] = document.getElementById("chLine" + 1);

	for (let i=0;i<6;i++) {
		var labels_ = [];
		for(let l_=0;l_<chart_column_num;l_++){
			labels_.push("");
		}
		if(eval('chLine' + i)) {
			window.chart[i] = new Chart(eval('chLine'+i), {
				type: 'line',
				data: {
					labels: labels_,
					datasets: [{
						data: [] }]},
				options: {
					scales: {
						yAxes: [{
							ticks: {
								beginAtZero: false
							}
						}]
					},
					legend: {
						display: false
					},
					// explorer에서의 차트 사이즈 안먹히는 문제로 수동모드로 사이즈 정해주기로 했습니다
					responsive: false
				}
			});
		}
	} // end-for
} // end-function create-chart-objects()
