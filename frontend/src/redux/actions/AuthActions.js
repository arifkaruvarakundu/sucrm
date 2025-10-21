import api from "../../../api_config"; // adjust path based on your folder structure

export const login = (email, password) => async dispatch => {
  try {
    dispatch({ type: "AUTH_REQUEST" });

    const { data } = await api.post("/login", { email, password });

    console.log("user_type", data)
    
    // Save token in localStorage
    localStorage.setItem("token", data.access_token);
    localStorage.setItem("email", data.email);
    localStorage.setItem("user_type", data.user_type);
    
    dispatch({
      type: "AUTH_SUCCESS",
      payload: { token: data.access_token, email: data.email },
    });
  } catch (error) {
    dispatch({
      type: "AUTH_FAIL",
      payload: error.response?.data?.detail || "Login failed",
    });
  }
};

export const register =
  (firstName, lastName, email, password, confirmPassword, user_type) =>
  async (dispatch) => {
    try {
      dispatch({ type: "AUTH_REQUEST" });

      const { data } = await api.post("/register", {
        first_name: firstName,
        last_name: lastName,
        email,
        password,
        confirm_password: confirmPassword,
        user_type,
      });

      localStorage.setItem("token", data.access_token);
      localStorage.setItem("email", data.email);
      localStorage.setItem("user_type", data.user_type)

      dispatch({
        type: "AUTH_SUCCESS",
        payload: { token: data.access_token, email: data.email },
      });
    } catch (error) {
      let message = "Registration failed";
      const detail = error.response?.data?.detail;

      if (Array.isArray(detail)) {
        message = detail.map((err) => err.msg).join(", ");
      } else if (typeof detail === "string") {
        message = detail;
      }

      dispatch({
        type: "AUTH_FAIL",
        payload: message,
      });
    }
  };


export const logout = () => dispatch => {
  localStorage.clear() 
  dispatch({ type: "LOGOUT" });
};
