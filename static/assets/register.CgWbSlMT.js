var u=Object.defineProperty;var p=(a,s,t)=>s in a?u(a,s,{enumerable:!0,configurable:!0,writable:!0,value:t}):a[s]=t;var i=(a,s,t)=>p(a,typeof s!="symbol"?s+"":s,t);import{r as o,k as g,j as e,i as x}from"./index.CNJJmEO6.js";import{L as h,X as l,G as c}from"./dialog.DCunRaEI.js";class f extends o.Component{constructor(){super();i(this,"handleInputChange",t=>{this.setState({[t.target.name]:t.target.value,passwordError:!1})});i(this,"handleCheckboxChange",t=>{this.setState({acceptedTerms:t.target.checked,termsError:!1})});i(this,"handleSubmit",t=>{const{password1:r,password2:n,acceptedTerms:d}=this.state;if(r!==n||!d){t.preventDefault(),r!==n&&this.setState({passwordError:!0}),d||this.setState({termsError:!0});return}});i(this,"openModal",()=>{this.setState({showModal:!0})});i(this,"closeModal",()=>{this.setState({showModal:!1})});const r=new URLSearchParams(window.location.search).get("registration_id")||"";this.state={registration_id:r,username:"",password1:"",password2:"",passwordError:!1,acceptedTerms:!1,termsError:!1,showModal:!1,csrfToken:""}}componentDidMount(){const t=g("csrftoken");this.setState({csrfToken:t})}render(){const{registration_id:t,passwordError:r,termsError:n,acceptedTerms:d,showModal:m}=this.state;return e.jsxs("div",{className:"flex min-h-full flex-col justify-center py-12 sm:px-6 lg:px-8",children:[e.jsx("div",{className:"mt-10 sm:mx-auto sm:w-full sm:max-w-[800px]",children:e.jsx("div",{className:"bg-white shadow sm:rounded-lg",children:e.jsxs("div",{className:"flex w-full flex-col md:flex-row",children:[e.jsxs("div",{className:"flex-1 bg-slate-700 px-6 pb-6 pt-12 text-white sm:rounded-t-lg md:rounded-lg md:rounded-r-none md:px-6 md:py-12",children:[e.jsxs("h1",{className:"mb-6 text-3xl font-bold",children:["RIXA",e.jsx("span",{className:"text-red-400",children:"."}),"ai"]}),e.jsxs("p",{className:"prose prose-invert text-sm text-gray-200",children:[e.jsx("h3",{children:"What is RIXA?"}),e.jsx("p",{children:"A research project."}),e.jsxs("p",{children:["...We present our concept and work in progress implementation of a new kind of XAI dashboard that uses a natural language chat. We specify 5 design goals for the dashboard and show the current state of our implementation. The natural language chat is the main form of interaction for our new dashboard. Through it the user should be able to control all important aspects of our dashboard... For more info see the paper"," ",e.jsx("a",{href:"https://publikationen.bibliothek.kit.edu/1000167428",children:"here"})]})]})]}),e.jsxs("div",{className:"flex-1 px-6 pb-12 pt-6 sm:rounded-b-lg md:rounded-lg md:px-6 md:py-12",children:[e.jsx("h1",{className:"mb-1 text-xl font-semibold",children:"Get started!"}),e.jsx("h2",{className:"mb-6 text-sm text-gray-400",children:"Create your account now."}),e.jsxs("form",{className:"space-y-6",action:"",method:"POST",onSubmit:this.handleSubmit,children:[e.jsx("input",{type:"hidden",name:"csrfmiddlewaretoken",value:this.state.csrfToken}),e.jsxs("div",{children:[e.jsx("label",{htmlFor:"username",className:"block text-sm font-medium leading-6 text-gray-600",children:"Username"}),e.jsx("div",{className:"mt-2",children:e.jsx("input",{type:"text",name:"username",id:"username",autoComplete:"username",onChange:this.handleInputChange,className:"block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6",required:!0})})]}),e.jsxs("div",{children:[e.jsx("label",{htmlFor:"password1",className:"block text-sm font-medium leading-6 text-gray-600",children:"Password"}),e.jsx("div",{className:"mt-2",children:e.jsx("input",{type:"password",name:"password1",id:"password1",autoComplete:"new-password",onChange:this.handleInputChange,className:"block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6",required:!0})})]}),e.jsxs("div",{children:[e.jsx("label",{htmlFor:"password2",className:"block text-sm font-medium leading-6 text-gray-600",children:"Confirm Password"}),e.jsx("div",{className:"mt-2",children:e.jsx("input",{type:"password",name:"password2",id:"password2",onChange:this.handleInputChange,className:"block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6",required:!0})}),r&&e.jsx("p",{className:"mt-2 text-sm text-red-600",children:"Passwords do not match."})]}),e.jsxs("div",{children:[e.jsx("label",{htmlFor:"invite",className:"block text-sm font-medium leading-6 text-gray-600",children:"Invite"}),e.jsx("div",{className:"mt-2",children:e.jsx("input",{type:"text",name:"registration_id",id:"registration_id",value:t,className:"block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"})})]}),e.jsxs("div",{children:[e.jsxs("label",{className:"flex items-start space-x-2",children:[e.jsx("input",{type:"checkbox",name:"acceptedTerms",onChange:this.handleCheckboxChange,className:"h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-600",required:!0}),e.jsxs("span",{className:"text-sm text-gray-600",children:["I accept the"," ",e.jsx("button",{type:"button",onClick:this.openModal,className:"text-indigo-600 underline hover:text-indigo-500",children:"terms and conditions"}),"."]})]}),n&&e.jsx("p",{className:"mt-2 text-sm text-red-600",children:"You must accept the terms and conditions."})]}),e.jsx("div",{children:e.jsx(h,{type:"submit",className:"flex w-full justify-center rounded-md bg-indigo-600 px-3 py-1.5 text-sm font-semibold leading-6 text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600",children:"Register"})})]})]})]})})}),e.jsx(l.Root,{show:m,as:o.Fragment,children:e.jsxs(c,{as:"div",className:"relative z-10",onClose:this.closeModal,children:[e.jsx(l.Child,{as:o.Fragment,enter:"ease-out duration-300",enterFrom:"opacity-0",enterTo:"opacity-100",leave:"ease-in duration-200",leaveFrom:"opacity-100",leaveTo:"opacity-0",children:e.jsx("div",{className:"fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity"})}),e.jsx("div",{className:"fixed inset-0 z-10 overflow-y-auto",children:e.jsx("div",{className:"flex min-h-full items-center justify-center p-4 text-center sm:p-0",children:e.jsx(l.Child,{as:o.Fragment,enter:"ease-out duration-300",enterFrom:"opacity-0 translate-y-4 sm:translate-y-0 sm:scale-95",enterTo:"opacity-100 translate-y-0 sm:scale-100",leave:"ease-in duration-200",leaveFrom:"opacity-100 translate-y-0 sm:scale-100",leaveTo:"opacity-0 translate-y-4 sm:translate-y-0 sm:scale-95",children:e.jsxs(c.Panel,{className:"relative transform overflow-hidden rounded-lg bg-white px-4 pb-4 pt-5 text-left shadow-xl transition-all sm:my-8 sm:w-full sm:max-w-lg sm:p-6 lg:max-w-3xl",children:[e.jsx("div",{children:e.jsxs("div",{className:"text-center",children:[e.jsx(c.Title,{as:"h3",className:"text-lg font-medium leading-6 text-gray-900",children:"Terms and Conditions"}),e.jsx("div",{className:"mt-2 flex justify-center text-sm text-gray-600",children:e.jsxs("div",{className:"prose",children:[e.jsx("h1",{children:"Privacy Policy (Art. 13 GDPR)"}),e.jsx("h2",{children:"1. Personal Data"}),e.jsx("p",{children:"For the purpose of your participation in several sessions of the experiment, we process your e-mail address as personal data. For the purpose of your participation in the study we collect and process your interaction data during the experiment, including chats and interaction speed. We also collect sociodemographic data (age, education level, profession). We strip any identifiable information before processing and publishing. However, given the challenges of automatic processing of chat data, there is a residual risk of re-identification in the dataset, therefore it might be possible to identify you as a natural person (data subject) if you accept to be included in the dataset. We therefore ask you to not include any personal data in the chat. To further minimize this risk, the dataset will be only made available to members of research and education institutions and only upon request. It will not be publicly available for everybody on the Internet. We will securely store the pseudonymized data and require interested researchers to register and get authorization before getting access to the dataset."}),e.jsx("p",{children:"Definition: An identifiable natural person is one who can be identified, directly or indirectly, in particular by reference to an identifier such as a name, an identification number, location data, an online identifier or to one or more factors specific to the physical, physiological, genetic, mental, economic, cultural or social identity of that natural person (Art. 4, No. 1 of the EU General Data Protection Regulation (GDPR))."}),e.jsx("h2",{children:"2. Controller"}),e.jsx("p",{children:"Responsible for the data processing according to Art. 4, No. 7 GDPR as well as other data protection regulations:"}),e.jsxs("p",{children:["Karlsruher Institut für Technologie (KIT) ",e.jsx("br",{}),"Kaiserstraße 12, 76131 Karlsruhe, Deutschland"," ",e.jsx("br",{}),"Tel.: +49 721 608-0 ",e.jsx("br",{}),"Fax: +49 721 608-44290 ",e.jsx("br",{}),"E-Mail: info@kit.edu"]}),e.jsx("p",{children:"The Karlsruhe Institute of Technology is a corporation governed by public law. It is represented by its president Prof. Jan S. Hesthaven."}),e.jsx("h2",{children:"3. Data processing"}),e.jsx("p",{children:"The activity data you have given us will be collected and stored for the purpose of scientific research. The specific processing purposes are to infer user needs, to enhance human-machine interaction."}),e.jsx("p",{children:"In order to operate the server, we need to record your IP address. It will not be associated with further recorded data and deleted automatically not later than 4 weeks after the recording."}),e.jsx("h2",{children:"4. Legal basis"}),e.jsx("p",{children:"The legal basis for the processing is your consent in accordance with Art. 6, par. 1, clause 1 (a) GDPR."}),e.jsx("p",{children:"According to Art. 7 par. 3 GDPR you have the right to withdraw your consent at any time with effect for the future. The consent is voluntary. There are no disadvantages for you if it is denied or withdrawn."}),e.jsx("h2",{children:"5. Your rights"}),e.jsx("p",{children:"You also have the following rights:"}),e.jsxs("ul",{children:[e.jsx("li",{children:"You have the right to obtain information from KIT about the data stored about you and/or to have incorrectly stored data corrected."}),e.jsx("li",{children:"You also have the right of erasure or limitation of processing or the right to object to processing."}),e.jsx("li",{children:"You have the right to withdraw your consent at any time, whereby the lawfulness of processing based on consent before its withdrawal is not affected. To assert these rights, please contact:"})]}),e.jsx("p",{children:"You also have the right to lodge a complaint with a supervisory authority about the processing of the personal data concerning you by Karlsruhe Institute of Technology. The Supervisory authority of KIT is:"}),e.jsx("p",{children:"The State Commissioner for Data Protection and Freedom of Information Baden-Württemberg (Landesbeauftragter für den Datenschutz und die Informationsfreiheit Baden-Württemberg)."}),e.jsx("h2",{children:"6. Data storage"}),e.jsx("p",{children:"The pseudonymized interaction and sociodemographic data will be kept indefinitely for the purpose of scientific research in order to guarantee the reproducibility of the research results obtained from the study."}),e.jsx("h2",{children:"7. Consent"}),e.jsx("p",{children:"I have read the above information and hereby consent to the collection, storage, and use of my data described in 1) for the purpose of scientific study."}),e.jsx("p",{children:"The consent is voluntary. There are no disadvantages if it is denied or withdrawn."}),e.jsx("h2",{children:"8. Publication"}),e.jsx("p",{children:"Additionally, to the above-mentioned scientific study, I also consent to the publication of my sociodemographic and activity data as raw data to other scientists for the purpose of advancing research."})]})})]})}),e.jsx("div",{className:"mt-5 sm:mt-6",children:e.jsx(h,{type:"button",className:"inline-flex w-full justify-center rounded-md border border-transparent bg-indigo-600 px-4 py-2 text-base font-medium text-white shadow-sm hover:bg-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 sm:text-sm",onClick:this.closeModal,children:"Close"})})]})})})})]})})]})}}x(document.getElementById("root")).render(e.jsx(o.StrictMode,{children:e.jsx(f,{})}));
