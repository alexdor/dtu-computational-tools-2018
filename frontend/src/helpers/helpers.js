export const parseJson = json => {
  try {
    return JSON.parse(json);
  } catch (e) {
    console.error(e);
    return e;
  }
};
