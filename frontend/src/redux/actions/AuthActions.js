import api from "../../../api_config"; // adjust path based on your folder structure

export const login = (email, password) => async dispatch => {
  try {
    dispatch({ type: "AUTH_REQUEST" });

    const { data } = await api.post("/login", { email, password });

    // Save token in localStorage
    localStorage.setItem("token", data.access_token);
    localStorage.setItem("email", data.email);

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

export const register = (firstName, lastName, email, password, confirmPassword) => async dispatch => {
  try {
    dispatch({ type: "AUTH_REQUEST" });

    const { data } = await api.post("/register", {
      first_name: firstName,
      last_name: lastName,
      email,
      password,
      confirm_password: confirmPassword,
    });

    // Save token in localStorage
    localStorage.setItem("token", data.access_token);
    localStorage.setItem("email", data.email);

    dispatch({
      type: "AUTH_SUCCESS",
      payload: { token: data.access_token, email: data.email },
    });
  } catch (error) {
    dispatch({
      type: "AUTH_FAIL",
      payload: error.response?.data?.detail || "Registration failed",
    });
  }
};

export const logout = () => dispatch => {
  localStorage.clear() 
  dispatch({ type: "LOGOUT" });
};
