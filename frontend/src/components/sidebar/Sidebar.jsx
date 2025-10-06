import React from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useDispatch } from 'react-redux'
import './sidebar.css'
import logo from '../../assets/images/logo of feeds.jpg'
import sidebar_items from '../../assets/JsonData/sidebar_routes.json'
import { useTranslation } from 'react-i18next';
import { logout } from '../../redux/actions/AuthActions'
    
const SidebarItem = props => {
    const { t } = useTranslation("side_bar");
    const active = props.active ? 'active' : ''

    return (
        <div className="sidebar__item">
            <div className={`sidebar__item-inner ${active}`}>
                <i className={props.icon}></i>
                <span>{t(props.title)}</span>
            </div>
        </div>
    )
}

const Sidebar = () => {
    
    const { t } = useTranslation("side_bar");
    const location = useLocation()
    const navigate = useNavigate()
    const activePath = location.pathname
    const dispatch = useDispatch()

    const handleLogout = () => {
        dispatch(logout())
        navigate("/")          // 👈 redirect to SignIn page
    }
    

    return (
        <div className='sidebar'>
            <div className="sidebar__logo">
                {/* <img src={logo} alt="company logo" />  */}
                {t("appName")}
            </div>
            <div className="sidebar__menu">
                {
                    sidebar_items
                        .filter(item => item.key !== 'logout')
                        .map((item, index) => (
                            <Link to={item.route} key={index}>
                                <SidebarItem
                                    title={item.key}
                                    icon={item.icon}
                                    active={item.route === activePath}
                                />
                            </Link>
                        ))
                }
            </div>
            <div className="sidebar__footer" onClick={handleLogout} style={{ cursor: 'pointer' }}>
                <SidebarItem
                    title={'logout'}
                    icon={'bx bx-log-out'}
                    active={false}
                />
            </div>
        </div>
    )
}

export default Sidebar
