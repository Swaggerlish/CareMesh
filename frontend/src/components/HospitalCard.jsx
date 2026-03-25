export default function HospitalCard({ hospital, onBook }) {
  return (
    <div className="card">
      <div className="card-header">
        <h3>{hospital.name}, {hospital.lga}, {hospital.state}</h3>
      </div>
      <p><strong>Address:</strong> {hospital.address}</p>
      <p><strong>Specialties:</strong> {hospital.specialties}</p>
      <p><strong>Available Facilities:</strong> {hospital.facilities ? hospital.facilities.join(', ') : `${hospital.services}, ${hospital.capabilities}`}</p>
      <button onClick={() => onBook(hospital)}>Book appointment</button>
    </div>
  )
}
