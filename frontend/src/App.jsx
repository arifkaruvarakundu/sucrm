import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import SignIn from './pages/SignIn'
import RegisterAdmin from './pages/Register'
import Dashboard from './pages/Landing'
import ProductAnalysis from './pages/ProductAnalysis'
import Layout from './components/layout/Layout'
// import ProductDetails from './pages/ProductDetails'
import ProductSalesGraph from './components/products/ProductSalesGraph'
import CustomerAnalysis from './pages/CustomerAnalysis'
import CustomerDetails from './pages/customerDetails'
import ProductOrderGraph from './components/customers/ProductOrderGraph'
import OrderAnalysis from './pages/OrderAnalysis'
import ChatAI from './components/chat_ai/chat_ai' 
// import ProtectedRoute from './components/ProtectedRoute'
import Messaging from './pages/Messaging'
import AnalyseExternalData from './pages/AnalyseExternalData'
import ExternalDataPage from './pages/DataUploadPage'
import DataTypeSelector from './pages/DataSelectionPage'
import MappingPage from './pages/Analysis_mapping'
import YourFiles from './pages/UserFiles'

function App() {
  return (
    <Router>
      <Routes>
        {/* Public routes */}
        <Route path="/" element={<ExternalDataPage />} />
        <Route path="/signin" element={<SignIn />} />
        <Route path="/register" element={<RegisterAdmin />} />
        <Route path="/dataSelection" element={<DataTypeSelector />} />
        <Route path="/mappingPage" element={<MappingPage />} />
        {/* Protected routes (wrapped inside Layout) */}
        {/* <Route element={<ProtectedRoute />}> */}
        <Route element={<Layout />}>
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/ProductAnalysis" element={<ProductAnalysis />} />
          {/* <Route path="/product/:id" element={<ProductDetails />} /> */}
          <Route path="/product-sales/:id" element={<ProductSalesGraph />} />
          <Route path="/CustomerAnalysis" element={<CustomerAnalysis />} />
          <Route path="/customer-details/:id" element={<CustomerDetails />} />
          <Route path="/productOrdergraph" element={<ProductOrderGraph />} />
          <Route path="/orderAnalysis" element={<OrderAnalysis />} />
          <Route path="/messaging" element={<Messaging />} />
          <Route path="/chat" element={<ChatAI />} />
          <Route path="/files" element={<YourFiles />} />
          {/* <Route path="/AnalyseExternalData" element={<AnalyseExternalData />} /> */}
        </Route>
        {/* </Route> */}
      </Routes>
    </Router>
  )
}

export default App
