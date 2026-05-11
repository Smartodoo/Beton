// /** @odoo-module **/
// import { patch } from "@web/core/utils/patch";

// import { Notebook } from "@web/core/notebook/notebook";

// const components = { Notebook };

// const rpc = require("web.rpc");

// var tab_style = 'horizontal';
// var tab_style_mobile = 'horizontal';


// rpc.query({
//     model: 'sh.back.theme.config.settings',
//     method: 'search_read',
//     domain: [['id','=',1]],
//     fields: ['tab_style','tab_style_mobile']
// }).then(function(data) {
//     if (data) {
// 		console.log("LLLLLLLLLLLLLLLl",data)
//     	 if(data[0]['tab_style']=='vertical'){
//     		 tab_style = 'vertical';
//     	 }
//     	 if(data[0]['tab_style_mobile']=='vertical'){
//     		 tab_style_mobile = 'vertical';
//     	 }
//     }
// });

// Notebook.template = "web.Notebook";
// Notebook.defaultProps = {
//     className: "",
//     orientation: "horizontal",
//     onPageUpdate: () => {},
// };
// Notebook.props = {
//     slots: { type: Object, optional: true },
//     pages: { type: Object, optional: true },
//     class: { optional: true },
//     className: { type: String, optional: true },
//     anchors: { type: Object, optional: true },
//     defaultPage: { type: String, optional: true },
//     orientation: { type: String, optional: true },
//     onPageUpdate: { type: Function, optional: true },
// };


